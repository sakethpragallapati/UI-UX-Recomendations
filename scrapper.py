from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException
)
from PIL import Image
import io
import time
import os
import json
import logging
from urllib.parse import urlparse
import concurrent.futures
from tqdm import tqdm

# --- 21-Class Two-Path Ontology ---
CLASSES = [
    # Generic Text-Based Elements (Requires OCR)
    'general_button', 'general_link', 'general_input', 'general_dropdown', 
    'general_label', 'general_checkbox', 'general_radio', 'general_textarea', 
    'general_menu_item', 'general_slider', 'general_image', 'general_video', 
    'general_iframe', 'general_form', 'general_table', 'general_clickable',
    # Specific Visual Icons (No OCR Needed)
    'icon_cart', 'icon_menu', 'icon_search', 'icon_profile', 'icon_close'
]

# --- Fully Merged & Deduplicated Websites Dictionary ---
WEBSITES = {
    'google_ecosystem': [
        "https://www.google.com", "https://support.google.com", "https://docs.google.com", 
        "https://maps.google.com", "https://drive.google.com", 
        "https://sites.google.com", "https://googleusercontent.com", "https://accounts.google.com", 
        "https://plus.google.com", "https://policies.google.com", "https://search.google.com", 
        "https://google.de", "https://google.com.br", "https://googleblog.com", "https://goo.gl", 
        "https://tools.google.com", "https://news.google.com", "https://developers.google.com", 
        "https://mail.google.com", "https://gstatic.com", "https://workspace.google.com", 
        "https://google.es", "https://photos.google.com", 
        "https://spotify.com", "https://google.fr", "https://get.google.com", 
        "https://picasaweb.google.com", "https://storage.googleapis.com", 
        "https://marketingplatform.google....", "https://google.co.uk", "https://google.it", 
        "https://myaccount.google.com", "https://adssettings.google.com", "https://google.co.jp", 
        "https://google.ca", "https://translate.google.com", "https://calendar.google.com", 
        "https://google.ru", "https://ggpht.com", "https://books.google.com", "https://ipv4.google.com", 
        "https://google.nl", "https://picasa.google.com", "https://google.co.th", 
        "https://video.google.com", "https://g.co", "https://blog.google", "https://ads.google.com", 
        "https://google.com.tw", "https://groups.google.com", "https://code.google.com", "https://google.pl",
        "https://play.google.com"
    ],
    'social_media_and_comms': [
        "https://linkedin.com", "https://t.me", "https://whatsapp.com", "https://facebook.com", 
        "https://vk.com", "https://live.com", "https://line.me", "https://myspace.com", 
        "https://tiktok.com", "https://wa.me", "https://ok.ru", "https://telegram.me", 
        "https://fb.com", "https://instagram.com", "https://discord.com", "https://twitter.com", 
        "https://pinterest.com", "https://discord.gg", "https://vkontakte.ru", "https://skype.com", 
        "https://fb.me", "https://weibo.com", "https://quora.com", "https://twimg.com", 
        "https://reddit.com", "https://m.me", "https://kakao.com", "https://taringa.net", "https://zoom.us",
        "https://pinterest.fr"
    ],
    'video_and_streaming': [
        "https://youtube.com", "https://youtu.be", "https://vimeo.com", "https://dailymotion.com", 
        "https://soundcloud.com", "https://ytimg.com", "https://deezer.com", "https://netflix.com", 
        "https://twitch.tv", "https://bandcamp.com", "https://gfycat.com", "https://last.fm", 
        "https://nicovideo.jp"
    ],
    'e_commerce': [
        "https://amazon.com", "https://amazon.de", "https://aliexpress.com", "https://amazon.co.jp", 
        "https://amazon.co.uk", "https://amazon.fr", "https://target.com", "https://walmart.com", 
        "https://ssl-images-amazon.com", "https://amzn.to", "https://alibaba.com", "https://ikea.com", 
        "https://ebay.com", "https://amazon.ca", "https://amazon.es", "https://rakuten.co.jp", 
        "https://stores.jp", "https://shopify.com", "https://bigcommerce.com"
    ],
    'news_and_journalism': [
        "https://bbc.co.uk", "https://cnn.com", "https://theguardian.com", "https://nytimes.com", 
        "https://bloomberg.com", "https://indiatimes.com", "https://elpais.com", "https://huffpost.com", 
        "https://independent.co.uk", "https://businessinsider.com", "https://wsj.com", 
        "https://usatoday.com", "https://huffingtonpost.com", "https://bbc.com", "https://estadao.com.br", 
        "https://washingtonpost.com", "https://forbes.com", "https://mirror.co.uk", 
        "https://dailymail.co.uk", "https://thesun.co.uk", "https://news.yahoo.com", 
        "https://reuters.com", "https://time.com", "https://abril.com.br", "https://cbsnews.com", 
        "https://telegraph.co.uk", "https://lemonde.fr", "https://newyorker.com", "https://thetimes.co.uk", 
        "https://search.yahoo.com", "https://cbc.ca", "https://clarin.com", "https://francetvinfo.fr", 
        "https://guardian.co.uk", "https://foxnews.com", "https://20minutos.es", "https://sfgate.com", 
        "https://espn.com", "https://lavanguardia.com", "https://sputniknews.com", "https://nypost.com", 
        "https://elmundo.es", "https://abcnews.go.com", "https://express.co.uk", "https://detik.com", 
        "https://t-online.de", "https://usnews.com", "https://smh.com.au", "https://dw.com", 
        "https://lefigaro.fr", "https://theatlantic.com", "https://nydailynews.com", "https://rtve.es", 
        "https://newsweek.com", "https://economist.com", "https://marca.com", "https://hindustantimes.com", 
        "https://npr.org", "https://mashable.com", "https://latimes.com", "https://rt.com", 
        "https://nbcnews.com", "https://ouest-france.fr", "https://standard.co.uk", "https://cnbc.com", 
        "https://buzzfeed.com", "https://apnews.com", "https://theglobeandmail.com", "https://europapress.es", 
        "https://euronews.com", "https://liberation.fr", "https://metro.co.uk", "https://sina.com.cn", 
        "https://nikkei.com", "https://repubblica.it", "https://ap.org", "https://news.com.au", 
        "https://scmp.com", "https://cbslocal.com", "https://focus.de", "https://boston.com", 
        "https://globo.com", "https://terra.com.br", "https://ig.com.br", "https://uol.com.br", 
        "https://spiegel.de", "https://lexpress.fr", "https://techcrunch.com", "https://engadget.com", 
        "https://vice.com", "https://hollywoodreporter.com", "https://variety.com", "https://wired.com", 
        "https://pcmag.com", "https://theconversation.com", "https://techradar.com", "https://sciencemag.org", 
        "https://people.com", "https://tmz.com", "https://ign.com", "https://theverge.com", 
        "https://gizmodo.com", "https://insider.com", "https://cnet.com", "https://radiofrance.fr"
    ],
    'education_and_reference': [
        "https://en.wikipedia.org", "https://es.wikipedia.org", "https://pt.wikipedia.org", 
        "https://fr.wikipedia.org", "https://ru.wikipedia.org", "https://de.wikipedia.org", 
        "https://it.wikipedia.org", "https://ja.wikipedia.org", "https://pl.wikipedia.org", 
        "https://id.wikipedia.org", "https://m.wikipedia.org", "https://www.wikipedia.org", 
        "https://wikimedia.org", "https://creativecommons.org", "https://wiley.com", "https://nature.com", 
        "https://researchgate.net", "https://archive.org", "https://britannica.com", 
        "https://cambridge.org", "https://springer.com", "https://oup.com", "https://arxiv.org", 
        "https://plos.org", "https://sciencedirect.com", "https://jstor.org", "https://academia.edu", 
        "https://unesco.org", "https://harvard.edu", "https://berkeley.edu", "https://stanford.edu", 
        "https://upenn.edu", "https://washington.edu", "https://jhu.edu", "https://utexas.edu", 
        "https://cornell.edu", "https://mit.edu", "https://ted.com", "https://howstuffworks.com", 
        "https://merriam-webster.com", "https://thefreedictionary.com", "https://doi.org", 
        "https://wikihow.com", "https://wikia.com", "https://fandom.com", "https://tvtropes.org", 
        "https://mayoclinic.org", "https://webmd.com", "https://psychologytoday.com", "https://scholastic.com"
    ],
    'government_and_organizations': [
        "https://europa.eu", "https://nih.gov", "https://who.int", "https://w3.org", "https://un.org", 
        "https://nasa.gov", "https://cdc.gov", "https://www.gov.br", "https://planalto.gov.br", 
        "https://www.gov.uk", "https://ca.gov", "https://whitehouse.gov", "https://icann.org", 
        "https://gnu.org", "https://justice.gov", "https://ftc.gov", "https://usgs.gov", 
        "https://unicef.org", "https://archives.gov", "https://nps.gov", "https://usda.gov", 
        "https://admin.ch", "https://privacyshield.gov", "https://canada.ca"
    ],
    'blogs_cms_and_builders': [
        "https://www.blogger.com", "https://wordpress.org", "https://bp.blogspot.com", 
        "https://files.wordpress.com", "https://draft.blogger.com", "https://www.weebly.com", 
        "https://jimdofree.com", "https://wp.com", "https://medium.com", "https://webnode.page", 
        "https://e-monsite.com", "https://www.over-blog.com", "https://www.wix.com", 
        "https://www.canalblog.com", "https://storage.canalblog.com", "https://www.livejournal.com", 
        "https://bloglovin.com", "https://mystrikingly.com", "https://gooyaabitemplates.com", 
        "https://themeforest.net", "https://joomla.org", "https://amebaownd.com", 
        "https://photos1.blogger.com", "https://bp0.blogger.com", "https://bp1.blogger.com", 
        "https://bp2.blogger.com", "https://substack.com", "https://slideshare.net", 
        "https://forms.gle", "https://public-api.wordpress.com"
    ],
    'tech_and_software': [
        "https://cloudflare.com", "https://microsoft.com", "https://apple.com", "https://mozilla.org", 
        "https://github.com", "https://adobe.com", "https://opera.com", "https://cpanel.net", 
        "https://samsung.com", "https://cpanel.com", "https://windows.net", "https://amazonaws.com", 
        "https://apache.org", "https://nginx.org", "https://nginx.com", "https://php.net", 
        "https://ea.com", "https://playstation.com", "https://ibm.com", "https://netlify.app", 
        "https://steampowered.com", "https://oracle.com", "https://salesforce.com", 
        "https://blackberry.com", "https://intel.com", "https://huawei.com", "https://android.com", 
        "https://java.com", "https://gsmarena.com", "https://sony.com", "https://stackoverflow.com", 
        "https://ietf.org", "https://softonic.com"
    ],
    'design_and_visuals': [
        "https://istockphoto.com", "https://pixabay.com", "https://shutterstock.com", 
        "https://freepik.com", "https://imageshack.us", "https://photobucket.com", "https://pexels.com", 
        "https://gettyimages.com", "https://flickr.com", "https://giphy.com", "https://canva.com", 
        "https://offset.com", "https://unsplash.com", "https://dreamstime.com", "https://gravatar.com"
    ],
    'files_and_cloud_utilities': [
        "https://dropbox.com", "https://bit.ly", "https://tinyurl.com", "https://yadi.sk", 
        "https://4shared.com", "https://mediafire.com", "https://mega.nz", "https://ziddu.com", 
        "https://sendspace.com", "https://rapidshare.com", "https://zippyshare.com", 
        "https://depositfiles.com", "https://addthis.com", "https://addtoany.com", "https://linktr.ee", 
        "https://box.com"
    ],
    'domains_and_hosting': [
        "https://dan.com", "https://brandbucket.com", "https://afternic.com", "https://hugedomains.com", 
        "https://domainmarket.com", "https://reg.ru", "https://buydomains.com", "https://ovh.com", 
        "https://ovh.net", "https://ovhcloud.com", "https://sedoparking.com", "https://sedo.com", 
        "https://000webhost.com", "https://home.pl", "https://plesk.com", "https://secureserver.net", 
        "https://timeweb.ru", "https://dropcatch.com", "https://alicdn.com", "https://akamaihd.net", 
        "https://sakura.ne.jp", "https://cointernet.com.co", "https://biglobe.ne.jp", "https://namecheap.com", 
        "https://godaddy.com"
    ],
    'search_engines_and_portals': [
        "https://www.yahoo.com", "https://bing.com", "https://yandex.ru", "https://yandex.com", 
        "https://goo.ne.jp", "https://naver.com", "https://msn.com", "https://aol.com", 
        "https://yahoo.co.jp", "https://rambler.ru", "https://mail.ru", "https://qq.com", 
        "https://liveinternet.ru", "https://hatena.ne.jp"
    ],
    'miscellaneous': [
        "https://paypal.com", "https://booking.com", "https://zendesk.com", "https://vistaprint.com", 
        "https://sky.com", "https://eventbrite.com", "https://disney.com", "https://statista.com", 
        "https://change.org", "https://trustpilot.com", "https://interia.pl", "https://viglink.com", 
        "https://biblegateway.com", "https://indiegogo.com", "https://mailchimp.com", "https://kickstarter.com", 
        "https://redbull.com", "https://about.com", "https://nationalgeographic.com", "https://nba.com", 
        "https://reverbnation.com", "https://com.com", "https://narod.ru", "https://justjared.com", 
        "https://justgiving.com", "https://weather.com", "https://fifa.com", "https://digg.com", 
        "https://bestfreecams.club", "https://histats.com", "https://people.com", "https://prezi.com", 
        "https://thenai.org", "https://clickbank.net", "https://gofundme.com", "https://pbs.org", 
        "https://abc.net.au", "https://ft.com", "https://alexa.com", "https://abc.es", "https://aboutads.info", 
        "https://networkadvertising.org", "https://allaboutcookies.org", "https://youronlinechoices.com", 
        "https://telegra.ph", "https://nhk.or.jp", "https://hp.com", "https://enable-javascript.com", 
        "https://feedburner.com", "https://netvibes.com", "https://cnil.fr", "https://instructables.com", 
        "https://tripadvisor.com", "https://disqus.com", "https://goodreads.com", "https://hubspot.com", 
        "https://office.com", "https://list-manage.com"
    ],
    'web_apps': [
        "https://slack.com", "https://www.evernote.com"
    ],
    'dev_tools': [
        "https://codesandbox.io", "https://codepen.io", "https://jsfiddle.net", 
        "https://replit.com", "https://jupyter.org", "https://www.jetbrains.com"
    ],
    'creative': [
        "https://www.photopea.com", "https://www.pixilart.com", 
        "https://www.remove.bg", "https://www.figma.com"
    ],
    'ai_platforms': [
        "https://huggingface.co", "https://www.kaggle.com", 
        "https://colab.research.google.com", "https://wandb.ai"
    ]
}


class UIScraper:
    def __init__(self, output_dir="yolo_dataset", timeout=15):
        self.output_dir = output_dir
        self.timeout = timeout
        self.processed_urls = set()
        self.failed_urls = set()
        
        self.setup_directories()
        self.setup_logging()
        
        self.stats = {
            'processed_urls': 0,
            'failed_urls': 0,
            'total_elements': 0,
            'elements_by_class': {class_name: 0 for class_name in CLASSES},
            'elements_by_category': {category: 0 for category in WEBSITES.keys()}
        }

    def setup_directories(self):
        # CHANGED: Output directly to raw images/labels folders (no train/ splits)
        self.images_dir = os.path.join(self.output_dir, "images")
        self.labels_dir = os.path.join(self.output_dir, "labels")
        for directory in [self.images_dir, self.labels_dir]:
            os.makedirs(directory, exist_ok=True)

    def get_element_label(self, element, class_name):
        try:
            aria_label = element.get_attribute("aria-label")
            title = element.get_attribute("title")
            placeholder = element.get_attribute("placeholder")
            value = element.get_attribute("value")
            text_content = element.text
            name = element.get_attribute("name")
            alt_text = element.get_attribute("alt") if element.tag_name == "img" else None
            
            label_text = (aria_label or title or placeholder or alt_text or text_content or value or name or "").strip()
            
            if label_text:
                if len(label_text) > 30:
                    label_text = label_text[:27] + "..."
                return f"{class_name}: {label_text}"
            return class_name
        except Exception:
            return class_name

    def get_class_id(self, tag_name, element_type, class_name, aria_label=None, title=None, alt=None):
        tag_name = str(tag_name).lower() if tag_name else ""
        class_name = str(class_name).lower() if class_name else ""
        element_type = str(element_type).lower() if element_type else ""
        aria_label = str(aria_label).lower() if aria_label else ""
        title = str(title).lower() if title else ""
        alt = str(alt).lower() if alt else ""
        
        # Helper to search all descriptive attributes
        def has_kw(kw):
            return kw in class_name or kw in aria_label or kw in title or kw in alt or kw in element_type
        
        # 1. CHECK SPECIFIC ICONS FIRST
        if has_kw('cart') or has_kw('basket') or has_kw('checkout'):
            return CLASSES.index('icon_cart')
        
        if has_kw('search') or has_kw('magnify'):
            return CLASSES.index('icon_search')
            
        if has_kw('menu') or has_kw('hamburger') or has_kw('nav-toggle'):
            return CLASSES.index('icon_menu')
            
        if has_kw('profile') or has_kw('user') or has_kw('account') or has_kw('avatar'):
            return CLASSES.index('icon_profile')
            
        if has_kw('close') or has_kw('dismiss') or class_name == 'close':
            return CLASSES.index('icon_close')

        # 2. FALLBACK TO GENERIC SHAPES
        if 'button' in class_name or tag_name == 'button' or element_type == 'button' or 'btn' in class_name:
            return CLASSES.index('general_button')
        elif tag_name == 'a' or element_type == 'link':
            return CLASSES.index('general_link')
        elif tag_name == 'input':
            if element_type == 'checkbox': return CLASSES.index('general_checkbox')
            elif element_type == 'radio': return CLASSES.index('general_radio')
            else: return CLASSES.index('general_input')
        elif tag_name == 'select' or 'dropdown' in class_name or element_type == 'combobox':
            return CLASSES.index('general_dropdown')
        elif tag_name == 'textarea': return CLASSES.index('general_textarea')
        elif tag_name == 'label': return CLASSES.index('general_label')
        elif 'slider' in class_name or element_type == 'slider': return CLASSES.index('general_slider')
        elif 'menu-item' in class_name or element_type == 'menuitem': return CLASSES.index('general_menu_item')
        elif 'clickable' in class_name: return CLASSES.index('general_clickable')
        elif tag_name == 'img' or 'image' in class_name: return CLASSES.index('general_image')
        
        return -1

    def get_element_info(self, driver, element, viewport_metrics):
        try:
            rect = driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                return { top: rect.top, left: rect.left, width: rect.width, height: rect.height };
            """, element)
            
            if rect['width'] == 0 or rect['height'] == 0:
                return None

            metrics = driver.execute_script("""
                return {
                    devicePixelRatio: window.devicePixelRatio || 1,
                    viewportWidth: window.innerWidth || document.documentElement.clientWidth,
                    viewportHeight: window.innerHeight || document.documentElement.clientHeight
                };
            """)
            
            device_pixel_ratio = metrics['devicePixelRatio']
            scale_x = viewport_metrics['width'] / metrics['viewportWidth']
            scale_y = viewport_metrics['height'] / metrics['viewportHeight']
            
            coordinates = {
                "x1": max(0, rect['left'] * scale_x * device_pixel_ratio),
                "y1": max(0, rect['top'] * scale_y * device_pixel_ratio),
                "x2": min(viewport_metrics['width'], (rect['left'] + rect['width']) * scale_x * device_pixel_ratio),
                "y2": min(viewport_metrics['height'], (rect['top'] + rect['height']) * scale_y * device_pixel_ratio)
            }
            
            if (coordinates['x2'] > coordinates['x1'] and coordinates['y2'] > coordinates['y1']):
                tag_name = element.tag_name
                element_type = element.get_attribute("type") or element.get_attribute("role")
                class_name = element.get_attribute("class") or ""
                aria_label = element.get_attribute("aria-label") or ""
                title = element.get_attribute("title") or ""
                alt_text = element.get_attribute("alt") if tag_name == "img" else ""
                text_content = element.text
                placeholder = element.get_attribute("placeholder")
                value = element.get_attribute("value")
                name = element.get_attribute("name")
                
                class_id = self.get_class_id(tag_name, element_type, class_name, aria_label, title, alt_text)
                
                if class_id != -1:
                    self.stats['total_elements'] += 1
                    self.stats['elements_by_class'][CLASSES[class_id]] += 1
                    
                    return {
                        "coordinates": coordinates,
                        "class_id": class_id,
                        "class_name": CLASSES[class_id],
                        "tag_name": tag_name,
                        "element_type": element_type,
                        "accessibility": {
                            "aria_label": aria_label,
                            "title": title,
                            "alt_text": alt_text,
                            "role": element.get_attribute("role")
                        },
                        "content": {
                            "text": text_content,
                            "placeholder": placeholder,
                            "value": value,
                            "name": name
                        },
                        "descriptive_label": self.get_element_label(element, CLASSES[class_id])
                    }
        except Exception:
            pass
        return None

    def setup_logging(self):
        file_handler = logging.FileHandler(os.path.join(self.output_dir, 'scraper.log'))
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.WARNING) 
        logging.basicConfig(level=logging.INFO, handlers=[file_handler, stream_handler])

    def get_elements(self, driver, viewport_metrics):
        elements_info = []
        elements = driver.find_elements(By.XPATH, """
            //*[
                self::a or self::button or self::input or self::select or 
                self::textarea or self::label or self::img or self::svg or self::i or
                self::*[@role='button' or @role='link' or @role='menuitem' or 
                        @role='slider' or @role='checkbox' or @role='radio' or 
                        @role='textbox' or @role='combobox' or @role='switch' or 
                        contains(@class, 'button') or contains(@class, 'btn') or 
                        contains(@class, 'icon') or contains(@class, 'menu-item')]
            ]
        """)
        
        for element in elements:
            try:
                element_info = self.get_element_info(driver, element, viewport_metrics)
                if element_info:
                    elements_info.append(element_info)
            except StaleElementReferenceException:
                continue
        return elements_info

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--force-device-scale-factor=1")
        options.add_argument("--log-level=3") 
        options.add_argument("--silent")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-crash-reporter")
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service()
        service.creation_flags = 0x08000000 
        return webdriver.Chrome(service=service, options=options)

    def process_url(self, url, category):
        if url in self.processed_urls:
            return
        
        driver = None
        try:
            driver = self.setup_driver()
            driver.set_page_load_timeout(self.timeout)
            driver.get(url)
            
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            driver.execute_script("document.body.style.zoom = '100%'")
            driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1.5)
            
            viewport_metrics = driver.execute_script("""
                return {
                    width: Math.max(document.documentElement.clientWidth, window.innerWidth || 0),
                    height: Math.max(document.documentElement.clientHeight, window.innerHeight || 0),
                    scrollX: window.pageXOffset,
                    scrollY: window.pageYOffset,
                    devicePixelRatio: window.devicePixelRatio || 1
                };
            """)
            
            elements_info = self.get_elements(driver, viewport_metrics)
            
            if elements_info:
                screenshot = driver.get_screenshot_as_png()
                self.save_data(url, category, elements_info, screenshot)
                self.processed_urls.add(url)
                self.stats['processed_urls'] += 1
                if category in self.stats['elements_by_category']:
                    self.stats['elements_by_category'][category] += len(elements_info)
            else:
                logging.warning(f"No elements found for {url}.")
                self.failed_urls.add(url)
                self.stats['failed_urls'] += 1
                
        except TimeoutException:
            logging.warning(f"Timeout on {url}.")
            self.failed_urls.add(url)
            self.stats['failed_urls'] += 1
        except Exception as e:
            logging.warning(f"Error processing {url}: {str(e)}")
            self.failed_urls.add(url)
            self.stats['failed_urls'] += 1
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def save_class_list(self):
        with open(os.path.join(self.output_dir, "classes.txt"), 'w') as f:
            for class_name in CLASSES:
                f.write(f"{class_name}\n")

    def save_statistics(self):
        stats_file = os.path.join(self.output_dir, "statistics.json")
        failed_urls_file = os.path.join(self.output_dir, "failed_urls.txt")
        
        with open(stats_file, 'w') as f:
            stats_data = {
                'timestamp': int(time.time()),
                'total_processed': self.stats['processed_urls'],
                'total_failed': self.stats['failed_urls'],
                'total_elements': self.stats['total_elements'],
                'elements_by_class': self.stats['elements_by_class'],
                'elements_by_category': self.stats['elements_by_category'],
                'processed_urls': list(self.processed_urls)
            }
            json.dump(stats_data, f, indent=2)
        
        with open(failed_urls_file, 'w') as f:
            for url in self.failed_urls:
                f.write(f"{url}\n")

    def save_data(self, url, category, elements_info, screenshot):
        try:
            domain = urlparse(url).netloc.replace('www.', '')
            filename = f"{category}_{domain}_{int(time.time())}"
            
            image = Image.open(io.BytesIO(screenshot))
            image_width, image_height = image.size
            
            image_path = os.path.join(self.images_dir, f"{filename}.png")
            image.save(image_path)
            
            annotation_path = os.path.join(self.labels_dir, f"{filename}.txt")
            with open(annotation_path, 'w') as f:
                for element in elements_info:
                    coords = element['coordinates']
                    
                    x_center = (coords['x1'] + coords['x2']) / (2 * image_width)
                    y_center = (coords['y1'] + coords['y2']) / (2 * image_height)
                    width = (coords['x2'] - coords['x1']) / image_width
                    height = (coords['y2'] - coords['y1']) / image_height
                    
                    x_center = max(0.0, min(1.0, x_center))
                    y_center = max(0.0, min(1.0, y_center))
                    width = max(0.0, min(1.0, width))
                    height = max(0.0, min(1.0, height))
                    
                    f.write(f"{element['class_id']} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
            
            metadata_path = os.path.join(self.labels_dir, f"{filename}_meta.json")
            with open(metadata_path, 'w') as f:
                metadata = {
                    'url': url,
                    'category': category,
                    'timestamp': int(time.time()),
                    'image_size': {'width': image_width, 'height': image_height},
                    'elements': elements_info,
                    'dataset_split': 'raw' # CHANGED: Updated metadata tag
                }
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error saving data for {url}: {str(e)}")
    
    def print_summary(self):
        print("\nScraping Summary:")
        print("=" * 50)
        print(f"Total URLs processed: {self.stats['processed_urls']}")
        print(f"Failed URLs: {self.stats['failed_urls']}")
        print(f"Total elements detected: {self.stats['total_elements']}")
        
        print("\nElements by category:")
        print("-" * 30)
        for category, count in self.stats['elements_by_category'].items():
            if count > 0:
                print(f"{category}: {count}")
        
        print("\nElements by class:")
        print("-" * 30)
        for class_name, count in self.stats['elements_by_class'].items():
            if count > 0:
                print(f"{class_name}: {count}")

    def run(self, max_workers=5):
        try:
            all_tasks = []
            for category, urls in WEBSITES.items():
                for url in urls:
                    all_tasks.append((url, category))
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self.process_url, url, category) for url, category in all_tasks]
                
                for _ in tqdm(concurrent.futures.as_completed(futures), total=len(all_tasks), desc="Processing websites"):
                    pass
            
            self.save_class_list()
            self.save_statistics()
            self.print_summary()
            
        except Exception as e:
            logging.error(f"Error during scraping: {str(e)}")
            raise

def main():
    import argparse
    parser = argparse.ArgumentParser(description="UI Element Scraper for YOLO Dataset")
    parser.add_argument("--output-dir", default="yolo_dataset", help="Output directory for dataset")
    parser.add_argument("--max-workers", type=int, default=5, help="Maximum concurrent workers")
    parser.add_argument("--timeout", type=int, default=15, help="Page load timeout in seconds")
    
    args = parser.parse_args()
    
    scraper = UIScraper(
        output_dir=args.output_dir,
        timeout=args.timeout
    )
    scraper.run(max_workers=args.max_workers)

if __name__ == "__main__":
    main()