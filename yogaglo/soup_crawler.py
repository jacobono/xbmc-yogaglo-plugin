from BeautifulSoup import BeautifulSoup

#from http import openUrl, convert_relative_to_absolute_url
from http import openUrl, convert_relative_to_absolute_url
from urllib import urlencode
from urlparse import urljoin
import re

class SoupCrawler(object):

    # Yoga Glo Base Url
    def __init__(self, yoga_glo_url):
        self.yoga_glo_url = yoga_glo_url
        self.classDescriptionAjaxUrl = convert_relative_to_absolute_url(yoga_glo_url,
                                            "/_ajax_get_class_description.php")

    # Get basic navigation information, cueing off of Category
    # inputs
    # category [1-4]
    # Teacher, Style, Level, Duration
    # Returns list of tuples (title, url, *imageUrl) 
    # *optional
    def get_yoga_glo_navigation_information(self, yoga_glo_category):
        menuList = [] # list of tuples to return
        yogaglo = openUrl(self.yoga_glo_url)
        soup = BeautifulSoup(''.join(yogaglo))
        navInfo = soup.find('li', id=yoga_glo_category).findAll('a')
        print navInfo

        for info in navInfo:
            infoTitle = info.contents[0]
            info_url = convert_relative_to_absolute_url(self.yoga_glo_url,
                                                        info['href'])
            menu = (infoTitle, info_url)

            # Looking at teachers, need images
            if yoga_glo_category == "2":
                teacherImageUrl = self.get_teacher_image_url(info_url)
                menu = menu + (teacherImageUrl,)

            menuList.append(menu)

        print "YogaGlo -- got all the navigation information for category: %s" % yoga_glo_category
        return menuList


        # Get teacher Image Url -- only available on teachers page
        # need to encode url properly in case their are utf-8 characters --
        # there are some. Noah Maze!
        # returns full URL to teacher image
    def get_teacher_image_url(self, teacher_url):
        teacher_page = openUrl(teacher_url)
        soup = BeautifulSoup(teacher_page)
        img_section = soup.find('section', attrs={'class': 'cf'}).div.img
        return convert_relative_to_absolute_url(self.yoga_glo_url,
                                                img_section['src'])

    def crawl_videos(self, url):
        html = openUrl(url)
        soup = BeautifulSoup(html)
        possible_video_sections = soup.findAll('section', attrs={'class':'cf'})
        for video_section in possible_video_sections:
            yoga_glo_classes_divs = video_section.findAll('div',
                                                 id=re.compile('^[0-9]+'))
            if yoga_glo_classes_divs:
                return yoga_glo_classes_divs

    def get_classes(self, url):
        classes = [] # return array of dictionaries
        video_divs = self.crawl_videos(url)
        for video_div in video_divs:
            class_cover_picture_url = video_div.a.img['src'].encode('utf-8')
            class_url = convert_relative_to_absolute_url(self.yoga_glo_url,
                                                         video_div.a['href'])
            class_length = video_div.findAll('div')[3].contents[0]
            class_id = video_div['id']
            class_information = self.get_yoga_class_description(class_id)
            class_information['url'] = class_url
            class_information['coverPicUrl'] = class_cover_picture_url
            class_information['duration'] = int(class_length.split(" ")[0])
            classes.append(class_information)

        return classes

    # Get the class description key information from the ajax request
    # not really formed well, but this is how they get it in their main pages
    # -- I must comply
    # input -- the class ID from yogaGlo designation
    # return a dictionary of important fields
    # title, secondLabel, plot, style, level, teacher
    def get_yoga_class_description(self, class_id):
        # AJAX query params to get description html
        query = urlencode({ 'id' : class_id, 't': 0 })
        url = urljoin(self.classDescriptionAjaxUrl, "?" + query)
        class_description = openUrl(url)
        soup = BeautifulSoup(class_description)
        style = soup.i.nextSibling
        # malformed HTML - sometimes missing a class title
        # default to the class style so you know this in xbmc menu
        # TODO something else here, like color it to make it different
        try:
            title = soup.b.contents[0]
        except:
            title = style

        level = soup.findAll('i')[1].nextSibling
        # any teachers from this ajax call are already expressed in unicode
        # not the \xe9, it takes percent encoded %C3%A9 to unicode \xc3\xa9
        teacher = soup.findAll('i')[2].nextSibling

        # Some class descriptions span multiple br's
        # key off the 'grayline' div and all text after that is a description
        fullDesc = ""
        grayline = soup.find('div', attrs={'class': 'grayline'})
        descriptionElements = grayline.findAllNext(text=True)
        for descElement in descriptionElements:
            fullDesc += descElement

        return {'title' : title,
                'secondLabel' :
                "Style: " + style + " Level: " + level,
                'plot' : fullDesc,
                'style' : style,
                'level' : level,
                'teacher' : teacher }

    #Get yoga-of-the-day title and info
    # return dictionary with {title, information}
    def get_yoga_of_the_day_title_and_info(self):
            url = openUrl(self.yoga_glo_url)
            yotd = BeautifulSoup(url)
            yotd_section = yotd.find('section',
                                            attrs={'class': 'home_vids'})
            yotd_info = yotd_section.findNext('p')

            return {'title' : yotd_section.h1.contents[0],
                    'information' : yotd_info.contents[0].encode('utf-8') }
