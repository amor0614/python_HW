import time
import os
import datetime
##擷取網頁資料
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ChromeOptions
import requests
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
## OCR
from PIL import Image
import pytesseract as tess
tess.pytesseract.tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe'
## mongodb
import pymongo

#連接mongo
client  = pymongo.MongoClient(host='localhost', port=27017)
#指定資料庫
db = client ['house']
#指定資料表
collection = db['591']

count_update = 0
#檢查過期資料(設定三天) 將資料改為需要重新查詢
check_list = collection.find({'is_get_detail':True}).batch_size(60000)
for check_obj in check_list :
    if int(datetime.datetime.now().timestamp()-check_obj['edit_at'].timestamp()) > (3*24*60*60) :
        update_obj = {
                        '_id':check_obj['_id'],
                        'url':check_obj['url'],
                        'region':check_obj['region'],
                        'lessor_name':check_obj['lessor_name'],
                        'lessor_Identity':check_obj['lessor_Identity'],
                        'contact_phone':check_obj['contact_phone'],
                        'static_phone':check_obj['static_phone'],
                        'houce_type':check_obj['houce_type'],
                        'houce_current':check_obj['houce_current'],
                        'gender_require':check_obj['gender_require'],
                        'is_get_detail':False,
                        'edit_at':datetime.datetime.now(),
                        'creat_at':check_obj['creat_at']
                }
        collection.replace_one(check_obj,update_obj,True)
        count_update = count_update + 1


print('超過三天需要更新共' + str(count_update) + '筆資料')
print('------------------------')





####第一部分 擷取物件URL
#臺北
url = 'https://rent.591.com.tw/?kind=0&region=1'

option = ChromeOptions()
option.add_argument('-headless')

task_url = [] ##任務列表
driver = webdriver.Chrome(options=option, executable_path='C:\\Users\\murk1\\Desktop\\chromedriver.exe') # 使用-Chrome
driver.get(url)
driver.find_element_by_css_selector('dd[data-id="1"]').click()#第一次進入頁面點選台北市
time.sleep(2)#休息2秒
region = driver.find_element_by_css_selector('span[class="areaTxt"]').text
count_target = 0
tStart = time.time()
#取得資料URL
while True: #跑完全部頁數
    task_list = [] ##每一次迴圈 重設任務列表
    if len(driver.find_elements_by_css_selector('div[class="accreditPop"][style="display: block;"]'))!=0:#如果有要求權限的div 點選允許
        driver.find_element_by_css_selector('div[class="accreditPop"] a[class="close"]').click()
    concent_list = driver.find_elements_by_css_selector('a[style][href*="rent-detail"][target^="_blank"]')#獲得該頁物件列表
    for concent in concent_list:
        if str(collection.find_one({'url':concent.get_attribute("href")})) == 'None': #檢查資料庫是否有相同的Task
            count_target = count_target + 1
            user_info = concent.find_element_by_xpath('../../p[3]/em').text.split(' ')
            task_list.append({'region':region,'lessor_name':user_info[1],'lessor_Identity':user_info[0],'url':concent.get_attribute("href"),'is_get_detail':False,'edit_at':datetime.datetime.now(),'creat_at':datetime.datetime.now()})
        else:
            continue
    if len(task_list) != 0 :
        collection.insert_many(task_list)#塞入每頁的物件
    #print(len(task_list))
    
    try :
        element = driver.find_elements_by_css_selector('a[class="pageNext last"]')
        if len(element) != 0:#判斷是否為最後一頁
            if driver.find_element_by_css_selector('span[class="areaTxt"]').text == '新北市':#如果是新北最後一頁 跳出迴圈
                break
            else:
                driver.execute_script('document.getElementById("areaBoxNew").style.display ="block"')#顯示表單
                time.sleep(1)
                driver.find_element_by_id('areaBoxNew').find_element_by_css_selector('a[data-id="3"][class="active"]').click()#切換到新北市 修改data-id 可以轉至其他縣市
                region = '新北市'
        else :#下一頁繼續蒐集資料
            driver.find_element_by_css_selector('a[class="pageNext"][href="javascript:;"]').click()
    except:#如果無法點擊下一頁紀錄error
        print('無法點擊下一頁')
    try :
        while len(driver.find_elements_by_css_selector('div[id="j_loading"][style*="display: block;"]')) != 0 :#載入頁面
            time.sleep(2)#每次迴圈休息2秒 等待載入頁面
        if len(task_list) != 0 :
            time.sleep(2)#防BAN
    except:
        print('無法擷取資料')
#最後關閉資源
tEnd = time.time()
print('台北市新北市共新增了'+str(count_target)+'筆資料')
tTotal = round((tEnd - tStart),2)
print ('總共執行'+str(tTotal)+'秒')
print('------------------------')
####第二部分 利用物件URL進行個別資料擷取
del_target = 0
count_task = 0
           
tStart = time.time()

task_list = collection.find({'is_get_detail':False}).batch_size(60000)
for task in task_list :
    
    count_task = count_task + 1
    #要求資料
    name = task['lessor_name'].lstrip().lstrip() #出租人
    identity = task['lessor_Identity'].lstrip().lstrip() #出租人身份
    static_phone = '-' #固定電話
    contact_phone = '-' #連絡電話
    houce_type = '-' #房屋型態
    houce_current = '-' #房屋現況
    gender_require = '-'#性別需求
    #額外資料
    task_url = task['url'];
    try:#抓資料內容  -  若失敗，繼續執行下一筆資料不進行擷取該資料
        #改為selenium擷取資料 節勪LOADING問題
        driver.get(task_url)
        html = driver.page_source
        Obj = BeautifulSoup(html,'lxml')
        
        #解決沒有固定電話問題
        if len(Obj.find_all('div', {'class': 'hidtel'})) != 0 : 
            static_phone = Obj.find('div', {'class': 'hidtel'}).get_text()
        else :
            static_phone = '-'
        detailInfo = Obj.find('div', {'class': 'detailInfo clearfix'}).find_all('li')
        detailInfo2 = Obj.find('ul', {'class': 'clearfix labelList labelList-1'}).find_all('li')
    except:
        print(task_url + ' 無法擷取詳細資料')
        #解決物件已經被移除問題
        if len(Obj.find_all('div', {'class': 'error-info'})) != 0 :
            title = Obj.find('div', {'class': 'error-info'}).find('div', {'class': 'title'}).get_text()
            if title.find('不存在') != -1:
                del_target = del_target + 1
                collection.delete_one(task)
                print('原因:'+task_url+'資料已被移除，執行:刪除資料庫資料')
        elif len(Obj.find_all('dl', {'class': 'error_img'})) != 0 :
            title = Obj.find('dl', {'class': 'error_img'}).get_text()
            if title.find('找不到') != -1:
                del_target = del_target + 1
                collection.delete_one(task)
                print('原因:'+task_url+'資料已被移除，執行:刪除資料庫資料')
        else:
            f = open('error_html.txt', "a+")
            f.write(task_url+'\n')
            f.write(html+'\n')
            f.write('------------------------------------------------\n')
            f.close()
        continue

    #擷取資料內容
    for Info in detailInfo :
        info_name = Info.get_text().split(':')[0].lstrip().lstrip()
        info_detail = Info.get_text().split(':')[1].lstrip().lstrip()
        if info_name.find('型態') != -1:
            houce_type = info_detail
        elif info_name.find('現況')!= -1 :
            houce_current = info_detail
    
    for Info in detailInfo2 :
        info_name = Info.get_text().split('：')[0].lstrip().lstrip()
        info_detail = Info.get_text().split('：')[1].lstrip().lstrip()
        if info_name.find('性別要求') != -1:
            gender_require = info_detail
            break
    
    #IMG PHONE - 判斷電話是否為圖片
    if len(Obj.find('span', {'class': 'num'}).find_all('img')) != 0: #連絡電話為圖片時進行OCR辨識
        contact_phone = Obj.find('span', {'class': 'num'}).find('img')['src']
        phone_img_url = Obj.find('span', {'class': 'num'}).find('img')['src']
        phone_img_url = 'http:'+phone_img_url
        if (os.path.exists('./img/') == False): # 檢查檔案路徑
            os.makedirs('./img/')
        img_name = './img/showPhone.png'
        #圖片為 PHP 產生之動態圖片 使用selenium進行網頁截圖
        try:
            driver.get(phone_img_url)
            driver.save_screenshot(img_name)
            #確定存檔 - 休息2秒
            time.sleep(2)
            #將圖片灰階後 將灰色pixel轉白，白pixel轉黑 (經測試-白底黑字較黑底白字容易辨識)
            images=Image.open('./img/showPhone.png')
            images=Image.open(img_name).convert('L')
            for i in range(images.size[0]):
                for j in range(images.size[1]):
                    if images.getpixel((i,j)) > 150 :
                        images.putpixel((i,j),0)
                    else :
                        images.putpixel((i,j),255)
            text=tess.image_to_string(images)
            contact_phone = text.replace(' ','')
        except:
            print('get image error')
            contact_phone = '-'                    
        #關閉資源
        images.close()
    else :
        try:
            contact_phone = Obj.find('span', {'class': 'num'}).get_text().lstrip().lstrip()
        except:
            print('get contact_phone error')
            contact_phone = '-'
    
    insert_obj = {
                        '_id':task['_id'],
                        'url':task_url,
                        'region':task['region'],
                        'lessor_name':name,
                        'lessor_Identity':identity,
                        'contact_phone':contact_phone,
                        'static_phone':static_phone,
                        'houce_type':houce_type,
                        'houce_current':houce_current,
                        'gender_require':gender_require,
                        'is_get_detail':True,
                        'edit_at':datetime.datetime.now(),
                        'creat_at':task['creat_at']
                }
    try:#更新資料庫
         tEnd = time.time()
         tTotal = round((tEnd - tStart),2)
         collection.replace_one(task,insert_obj,True)
         count_task = count_task + 1
    except:
        print('資料庫操作問題')
    time.sleep(1)#每次迴圈休息1秒 防BAN

tEnd = time.time()


tTotal = round((tEnd - tStart),2)

print ('done')
print('更新了' + str(count_task) + '筆資料')
print('移除了' + str(del_target) + '筆資料')
print ('總共執行'+str(tTotal)+'秒')
print('------------------------')

driver.quit()
