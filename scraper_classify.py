from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from urllib.parse import urlparse
import time
import os
import random
import logging
import concurrent.futures
from tqdm import tqdm

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

class ClassificationScraper:
    def __init__(self, output_dir="website_dataset", timeout=15):
        self.output_dir = output_dir
        self.timeout = timeout
        self.setup_directories()
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

    def setup_directories(self):
        """Creates the strict train/val folder structure YOLOv8-cls requires."""
        for split in ['train', 'val']:
            for category in WEBSITES.keys():
                os.makedirs(os.path.join(self.output_dir, split, category), exist_ok=True)

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3") 
        options.add_argument("--silent")
        options.add_argument("--disable-logging")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        service = Service()
        service.creation_flags = 0x08000000 
        return webdriver.Chrome(service=service, options=options)

    def process_url(self, url, category):
        driver = None
        try:
            driver = self.setup_driver()
            driver.set_page_load_timeout(self.timeout)
            driver.get(url)
            
            WebDriverWait(driver, self.timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2) # Give it a moment to render JS components
            
            # Randomly sort into train (80%) or val (20%)
            split = "train" if random.random() < 0.8 else "val"
            
            domain = urlparse(url).netloc.replace('www.', '')
            filename = f"{domain}_{int(time.time())}.png"
            filepath = os.path.join(self.output_dir, split, category, filename)
            
            # Take screenshot
            driver.get_screenshot_as_file(filepath)
            
        except TimeoutException:
            logging.warning(f"Timeout: {url}")
        except Exception as e:
            logging.warning(f"Failed: {url} - {str(e)}")
        finally:
            if driver:
                driver.quit()

    def run(self, max_workers=5):
        print(f"📸 Starting Classification Scraping (Splitting to Train/Val)...")
        tasks = [(url, category) for category, urls in WEBSITES.items() for url in urls]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.process_url, url, cat) for url, cat in tasks]
            for _ in tqdm(concurrent.futures.as_completed(futures), total=len(tasks)):
                pass
        print("✅ Dataset generated perfectly for YOLOv8 Classification!")

if __name__ == "__main__":
    scraper = ClassificationScraper()
    scraper.run(max_workers=4)