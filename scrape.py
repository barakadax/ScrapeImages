import bs4
import json
import pathlib
import requests
import argparse
import validators
from typing import Optional
from collections import deque


class scraper(object):
    def __init__(self) -> None:
        self._counter: int = 1
        self._sites_visited: set = set()
        self._result_json: list[dict] = list()
        self._start_dir: pathlib.Path = pathlib.Path('./')
        self._invalid_HTML_url: deque = deque(maxlen=1000)
        self._invalid_images_url: deque = deque(maxlen=1000)
        self._invalid_chars_for_naming: str = "\\/:*?\"<>|\0&%"

    def _get_page_data(self, url: str) -> bs4.BeautifulSoup:
        if not url or not validators.url(url):
            print(f"<<< URL: \"{url}\" is empty input or not a real website URL, aborting this URL run.")
            return None
        page_data = requests.get(url)
        if page_data.is_redirect:
            print(f"<<< URL: \"{url}\" is redirecting to a different website, aborting this URL run for security measures.")
            return None
        elif page_data.status_code != 200:
            print(f"<<< URL: \"{url}\" has returned response: {page_data.status_code}, aborting this URL run.")
            return None
        elif 'html' not in page_data.headers['content-type']:
            self._invalid_HTML_url.append(url)
            print(f"<<< URL: \"{url}\" site is not html type website, aborting this URL run.")
            return None
        return bs4.BeautifulSoup(page_data.text, 'html.parser')

    def _search_different_links(self, parsered_page_data: bs4.BeautifulSoup, depth: int) -> None:
        links = parsered_page_data.find_all('a')
        for site_to_scrape in links:
            url = site_to_scrape.get('href', "")
            if url in self._invalid_HTML_url:
                print(f"<<< Link: {url} was already detected as not valid HTML site, skipping this link.")
                continue
            if url and validators.url(url):
                self._internal_logic(url, depth - 1)

    def _get_folder_name(self, url: str) -> str:
        url = url.replace("http://", '').replace("https://", '')
        for illegal_char in self._invalid_chars_for_naming:
            url = url.replace(illegal_char, '')
        return url.strip()[:100]

    def _create_dir(self, folder_name: str) -> pathlib.Path:
        new_path: pathlib.Path = self._start_dir.joinpath(folder_name)
        if not new_path.exists():
            print(f"<<< Created new folder: {folder_name}")
            new_path.mkdir()
        else:
            if not new_path.is_dir():
                raise Exception(f'<<< Same folder name: {folder_name} already exists but not as a folder, halts this site scraping')
            print(f"<<< Folder {folder_name} was already existing")
        return new_path

    def _normalize_image_name(self, image_name: str) -> str:
        if image_name:
            for illegal_char in self._invalid_chars_for_naming:
                image_name = image_name.replace(illegal_char, '')
        else:
            print("<<< Couldn\'t get image name, random name was given.")
            image_name = "randomImageScrapedFromWebsite" + str(self._counter)
            self._counter += 1
        return image_name + ".jpeg"

    def _get_image_url(self, image: bs4.element.Tag, url: str) -> Optional[str]:
        image_source_url = image.get('src', image.get('data-src', ""))
        if not image_source_url:
            return None

        if not validators.url(image_source_url):
            if url[:-1] != '/' and image_source_url[0] != '/':
                image_source_url = '/' + image_source_url
            image_source_url = url + image_source_url

        if not validators.url(image_source_url):
            print(f"<<< Invalid image url: {url}")
            return None
        return image_source_url

    def _is_image(self, response: requests.Response) -> bool:
        if response.is_redirect:
            print(f"<<< Image redirecting to a different website, won't continue to download this image: {response.url}")
            return False
        elif response.status_code != 200:
            print(f"<<< Couldn\'t reach {response.url} --- Got {response.status_code} as response.")
            return False
        elif 'image' not in response.headers['content-type']:
            self._invalid_images_url.append(response.url)
            print(f"<<< URL: {response.url} is not an image url site.")
            return False
        return True

    def _get_image_response(self, url: str) -> Optional[requests.models.Response]:
        if url in self._invalid_images_url:
            print(f"<<< Site {url} already been checked and is not an image site.")
            return None
        response = requests.get(url)
        if not self._is_image(response):
            return None
        return response

    def _save_image(self, current_folder: pathlib.Path, image_name: str, image_data: requests.models.Response) -> None:
        with current_folder.joinpath(image_name).open('wb') as newPicture:
            newPicture.write(image_data.content)

    def _download_images(self, images_list: list[bs4.element.Tag], url: str, depth: int, current_folder: pathlib.Path) -> None:
        for image in images_list:
            image_url = self._get_image_url(image, url)
            if not image_url:
                continue
            image_response = self._get_image_response(image_url)
            if not image_response:
                continue
            image_name = self._normalize_image_name(image.get('alt', ""))
            self._save_image(current_folder, image_name, image_response)
            self._result_json.append({'websiteURL': url, 'imageSource': image_url, 'depth': depth})
            print(f"<<< Downloaded: {image_name} --- from: {image_url}")

    def _remove_folder_if_empty(self, url: str, current_folder: pathlib.Path) -> bool:
        if len(list(current_folder.iterdir())) == 0:
            current_folder.rmdir()
            return True
        return False

    def _internal_logic(self, url: str, depth: int) -> None:
        if url in self._sites_visited:
            print(f"<<< Already visited in {url}")
            return
        else:
            self._sites_visited.add(url)
        self._counter = 1
        parsered_page_data = self._get_page_data(url)
        if not parsered_page_data:
            return
        if depth != 0:
            self._search_different_links(parsered_page_data, depth)
        images_list = parsered_page_data.find_all('img')
        if not images_list:
            return
        folder_name = self._get_folder_name(url)
        if not folder_name:
            return
        new_path: pathlib.Path = self._create_dir(folder_name)
        self._download_images(images_list, url, depth, new_path)
        if self._remove_folder_if_empty(url, new_path):
            print(f"<<< Didn\'t download any photo for {url} deleting folder: {new_path.name}", end='\n\n')
        else:
            print(f"<<< Done downloading images from {url}", end='\n\n')

    def _save_JSON(self) -> None:
        with open('results.json', 'w', encoding='utf-8') as result_file:
            json.dump(self._result_json, result_file)
        print("<<< Saved file with: website url, image url and depth of search for each image that was downloaded.")

    def execute(self, url: str, depth: int) -> None:
        if depth < 0:
            raise Exception("<<< Number must be positive.")
        self._internal_logic(url, depth)
        self._save_JSON()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Web scraper")
    parser.add_argument('url', type=str)
    parser.add_argument('depth', type=int)
    args = parser.parse_args()
    run = scraper()
    run.execute(args.url, args.depth)
