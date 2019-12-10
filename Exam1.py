import os
import pandas as pd

#樓層轉換數字
def trans_level(level):
    num_level = level.split('層')[0]
    digit = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    num = 0
    if num_level :
        id_h, id_d = num_level.find('百'),num_level.find('十')

    if id_h != -1 :
        num = num + digit[num_level[id_h - 1:id_h]]*100
    if id_d != -1 :
        if num_level[id_d - 1:id_d] in digit:
            num = num + digit[num_level[id_d - 1:id_d]]*10
        else :
            num = num + 10
    if num_level[-1] in digit:
        num  = num + digit[num_level[-1]]
    return num

def re_trans_level(num_level):
    id_h = int(num_level/100)
    id_d = int((num_level%100)/10)
    id_dig = int(num_level%10)
    digit = {1 : '一', 2 : '二', 3 : '三', 4: '四', 5 : '五', 6: '六', 7: '七', 8: '八', 9: '九'}
    str_level = ""
    
    if id_h !=0 :
        str_level = str_level + digit[id_h] + '百'
    if id_d !=0 :
        if id_h !=0 :
            str_level = str_level + digit[id_d] + '十'
        else:
            if id_d == 1:
                str_level = str_level +  '十'
            else:
                str_level = str_level + digit[id_d] + '十'
    if id_dig !=0 :
        str_level = str_level + digit[id_dig]
    str_level = str_level + '層'
    return str_level




# 讀檔
df_a = pd.read_csv('a_lvr_land_a.csv')  
df_b = pd.read_csv('b_lvr_land_a.csv')  
df_e = pd.read_csv('e_lvr_land_a.csv')  
df_f = pd.read_csv('f_lvr_land_a.csv')  
df_h = pd.read_csv('h_lvr_land_a.csv')  
df_all = pd.DataFrame()


#移除row=0後(因為是英文columns)，進行合併資料
df_all = df_all.append(df_a.drop([0,0]))
df_all = df_all.append(df_b.drop([0,0]))
df_all = df_all.append(df_e.drop([0,0]))
df_all = df_all.append(df_f.drop([0,0]))
df_all = df_all.append(df_h.drop([0,0]))

######filter_a.csv######
temp_df_all = df_all
for index, row in temp_df_all.iterrows():#轉換層數為數字
    row['總樓層數'] = trans_level(str(row['總樓層數']))
    
acsv = df_all[(df_all['主要用途']=='住家用')&(df_all['建物型態'].str.contains("住宅大樓")==True)&(df_all['總樓層數']>=13)] ##塞選資料

for index, row in acsv.iterrows():#將樓層轉回文字
    row['總樓層數'] = re_trans_level(row['總樓層數'])
if ~(os.path.isfile('./CSV')):
     os.mkdir('./CSV')
#匯出CSV
acsv.to_csv(path_or_buf ='CSV/filter_a.csv',index=True,encoding='UTF-8')


######filter_b.csv######

#總件數
total_case = len(df_all.index)
#總車位數
total_car_space = 0
#合計總價元
total_price = 0
#合計車位總價元
total_car_price = 0

for index, row in df_all.iterrows():
    #總車位數 (透過交易筆棟數)
    strtransaction = str(row['交易筆棟數'])
    idx_c = strtransaction.find('車位')
    if idx_c != -1 :
        total_car_space = total_car_space + int(strtransaction[idx_c+2:idx_c+5])
    #合計總價元
    total_price = total_price + int(row['總價元'])
    #合計車位總價元 
    total_car_price = total_car_price + int(row['車位總價元'])


#計算平均總價元 (平均總價元 = 合計總價元/總件數)
avg_price = total_price/total_case
#計算平均車位總價元 (平均車位總價元 = 合計車位總價元/總車位數)
avg_car_price = total_car_price/total_car_space

#轉換為DataFrame
bcsv = pd.DataFrame({'總件數':total_case,'總車位數':total_car_space,'平均總價元':avg_price,'平均車位總價元':avg_car_price},index=[0])
#匯出CSV
bcsv.to_csv(path_or_buf ='CSV/filter_b.csv',index=True,encoding='UTF-8')


print('done')









    
