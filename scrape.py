import os
import sys
import json
import requests
import validators
from typing import Optional
from bs4 import BeautifulSoup


class scraper(object):
    def __init__(self) -> None:
        self.__counter = 1
        self.__result_json: list[dict] = list()
        self.__start_dir = os.getcwd()
        self.__invalid_chars_for_naming = "\\/:*?\"<>|\0&"

    def __get_page_data(self, url: str) -> BeautifulSoup:
        if not url or not validators.url(url):
            print(
                f"<<< URL: \"{url}\" is empty input or not a real website url, aborting this url run.")
            return None
        page_data = requests.get(url)
        if page_data.is_redirect:
            print(
                f"<<< URL: \"{url}\" is redirecting to a different website, aborting this url run for security measures.")
            return None
        elif page_data.status_code != 200:
            print(
                f"<<< URL: \"{url}\" has returned response: {page_data.status_code}, aborting this url run.")
            return None
        elif 'html' not in page_data.headers['content-type']:
            print(
                f"<<< URL: \"{url}\" site is not html type website, aborting this url run.")
            return None
        return BeautifulSoup(page_data.text, 'html.parser')

    def __search_different_links(self, parsered_page_data: BeautifulSoup, depth: int) -> None:
        links = parsered_page_data.find_all('a')
        for site_to_scrape in links:
            url = site_to_scrape.get('href', "")
            if url and validators.url(url):
                self.__internal_logic(url, depth - 1)

    def __get_folder_name(self, url: str) -> str:
        url = url.replace("http://", '')
        url = url.replace("https://", '')
        for illegal_char in self.__invalid_chars_for_naming:
            url = url.replace(illegal_char, '')
        return url.strip()

    def __create_dir(self, folder_name: str) -> None:
        new_path = os.path.join(self.__start_dir, folder_name)
        if not os.path.exists(new_path):
            print(f"<<< Created new folder: {folder_name}")
            os.mkdir(new_path)
        else:
            print(f"<<< Folder {folder_name} was already existing")
        os.chdir(new_path)

    def __get_image_name(self, image_name: str) -> str:
        if image_name:
            for illegal_char in self.__invalid_chars_for_naming:
                image_name = image_name.replace(illegal_char, '')
        else:
            print("<<< Couldn\'t get image name, counter random name was given.")
            image_name = "randomImageScrapedFromWebsite" + str(self.__counter)
            self.__counter += 1
        return image_name + ".jpeg"

    def __get_image_url(self, image: BeautifulSoup, url: str) -> str:
        image_source_url = image.get('src', image.get('data-src', ""))
        if not validators.url(image_source_url):
            image_source_url = url + image_source_url
        if not validators.url(image_source_url):
            print(f"<<< Invalid image url: {url}")
            return ''
        return image_source_url

    def __get_image_data(self, url: str) -> Optional[requests.models.Response]:
        image_data = requests.get(url)
        if image_data.is_redirect:
            print(
                f"<<< Image redirecting to a different website, won't continue to download this image: {url}")
            return None
        elif image_data.status_code != 200:
            print(
                f"<<< Couldn\'t reach {url} --- Got {image_data.status_code} as response.")
            return None
        elif 'image' not in image_data.headers['content-type']:
            print(f"<<< URL: {url} is not an image url site.")
            return None
        return image_data

    def __save_image(self, image_name: str, image_data: requests.models.Response) -> None:
        with open(image_name, 'wb') as newPicture:
            newPicture.write(image_data.content)

    def __download_images(self, images_list: list, url: str, depth: int) -> None:
        for image in images_list:
            image_url = self.__get_image_url(image, url)
            if not image_url:
                continue
            image_data = self.__get_image_data(image_url)
            if not image_data:
                continue
            image_name = self.__get_image_name(image.get('alt', ""))
            self.__save_image(image_name, image_data)
            self.__result_json.append(
                {'websiteURL': url, 'imageSource': image_url, 'depth': depth})
            print(f"<<< Downloaded: {image_name} --- from: {image_url}")

    def remove_empty_folder(self, url: str, folder_name: str) -> None:
        print(
            f"<<< Didn\'t download any photo for {url} deleting folder: {folder_name}", end='\n\n')
        os.chdir(self.__start_dir)
        os.rmdir(os.path.join(self.__start_dir, folder_name))

    def __internal_logic(self, url: str, depth: int) -> None:
        parsered_page_data = self.__get_page_data(url)
        if not parsered_page_data:
            return
        if depth != 0:
            self.__search_different_links(parsered_page_data, depth)
        images_list = parsered_page_data.find_all('img')
        if not images_list:
            return
        folder_name = self.__get_folder_name(url)
        if not folder_name:
            return
        self.__create_dir(folder_name)
        self.__download_images(images_list, url, depth)
        if len(os.listdir(os.getcwd())) == 0:
            self.remove_empty_folder(url, folder_name)
        else:
            print(f"<<< Done downloading images from {url}", end='\n\n')

    def __save_JSON(self) -> None:
        os.chdir(self.__start_dir)
        # TO:DO change to write binary 'wb'
        with open('results.json', 'w', encoding='utf-8') as result_file:
            json.dump(self.__result_json, result_file)
        print("<<< Saved file with: website url, image url and depth of search for each image that was downloaded.")

    def execute(self, url: str, depth: str) -> None:
        search_depth = int(depth)
        if search_depth < 0:
            raise Exception("<<< Number must be positive.")
        self.__internal_logic(url, search_depth)
        self.__save_JSON()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        exit(1)
    run = scraper()
    run.execute(sys.argv[1], sys.argv[2])
    exit(0)
