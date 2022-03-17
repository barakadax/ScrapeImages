import os
import sys
import json
import requests
import validators
from bs4 import BeautifulSoup

class scrape_pictures(object):
    def __init__(self) -> None:
        self.__counter = 1
        self.__result = list()
        self.__start_dir = os.getcwd()
        self.__invalid_chars_for_file_name = "\\/:*?\"<>|\0"

    def execute(self, url, depth) -> None:
        self.__internal_logic(url, depth)
        os.chdir(self.__start_dir)
        self.__save_JSON()
        print("<<< Done.")

    def __internal_logic(self, url, depth) -> None:
        os.chdir(self.__start_dir)
        page_data = self.__get_page_data(url)
        if not page_data:
            return
        parsered_data = BeautifulSoup(page_data.text, 'html.parser')
        if depth != 0:
            self.__recursive_depth_search(parsered_data, depth)
        folder_name = self.__get_folder_name(parsered_data)
        if not folder_name:
            return
        folder_path = self.__create_dir(folder_name)
        if not folder_path:
            return
        os.chdir(folder_path)
        picture_list = self.__get_picture_list(parsered_data)
        if not picture_list:
            return
        self.__download_pictures(url, picture_list, depth)

    def __get_page_data(self, url) -> object: 
        if not url and not validators.url(url):
            print("<<< Please enter a valid website URL.")
            return None
        page_data = requests.get(url)
        if page_data.is_redirect:
            print("<<< Something awful had happen, you have been redirected to a different website.")
            return None
        elif page_data.status_code != 200:
            print("<<< Something awful had happen, site can\'t be reached.")
            return None
        return page_data

    def __recursive_depth_search(self, parsered_data, depth) -> None:
        links = parsered_data.find_all('url')
        for site_to_scrape in links:
            self.__internal_logic(site_to_scrape.content, depth - 1)

    def __get_folder_name(self, parsered_data) -> str:
        folder_name = parsered_data.title.text
        if not folder_name:
            print("<<< Something awful had happen, website doesn\'t have name, can\'t create folder without name.")
            return None
        for illegal_char in self.__invalid_chars_for_file_name:
            folder_name = folder_name.replace(illegal_char, '')
        return folder_name

    def __create_dir(self, folder_name) -> str:
        if not os.path.exists(os.path.join(os.getcwd(), folder_name)):
            try:
                os.mkdir(os.path.join(os.getcwd(), folder_name))
                print("<<< Created a folder for the photos name ", folder_name)
            except OSError:
                print("<<< Something awful had happen, couldn\'t create folder.")
                return None;
        else:
            print("<<< Folder already exists to download pictures and save into.")
        return os.path.join(os.getcwd(), folder_name)

    def __get_picture_list(self, parsered_data) -> list:
        picture_list = parsered_data.find_all('img')
        if len(picture_list) == 0:
            print("<<< Website page doesn\'t have any pictures in it.")
            return None
        return picture_list

    def __get_picture_name(self, pic_data) -> str:  # command injection safe?
        if pic_data:
            image_name = pic_data
            for illegal_char in self.__invalid_chars_for_file_name:
                image_name = image_name.replace(illegal_char, '')
        else:
            image_name = "randomImageScrapedFromWebsite" + str(self.__counter)
            self.__counter += 1
        return image_name

    def __validate_picture_data(self, image_data) -> bool:
        if image_data.is_redirect:
            print("<<< Something awful had happen, you have been redirected to a different website.")
            return True
        elif image_data.status_code != 200:
            print("<<< Something awful had happen, photo can\'t be reached.")
            return True
        return False

    def __save_picture(self, image_name, image_data) -> None:  # what if file exists? override or skip?
        with open(image_name + '.jpeg', 'wb') as newPicture:
            newPicture.write(image_data.content)
            print("<<< Downloaded: " + image_name)

    def __download_pictures(self, url, picture_list, depth) -> None:
        for image in picture_list:
            image_name = self.__get_picture_name(image['alt'])
            
            image_source = image['src']
            image_link = url + image_source
            image_data = requests.get(url + image_source)
            if self.__validate_picture_data(image_data):
                image_link = image_source
                image_data = requests.get(image_source)
                if self.__validate_picture_data(image_data):
                    print(f"<<< Couldn\'t get the picture: {image_name} from the internet with relative and full url.")
                    continue
            
            self.__save_picture(image_name, image_data)
            self.__result.append(
                {
                    'imageUrl' : image_link,
                    'sourceUrl' : url,
                    'depth' : depth
                }
            )
    
    def __save_JSON(self):
        with open('results.json', 'w', encoding='utf-8') as result_file:
            json.dump(self.__result, result_file)
        print("<<< Saved JSON with data about picture source.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("<<< Missing or too many parameters were given.\n<<< Done.")
    download_pictures = scrape_pictures()
    download_pictures.execute(sys.argv[1], sys.argv[2])
    exit(0)
