# conding : utf-8

import argparse
import os
import pandas as pd
import sys
import yaml
import datetime
import pprint

from pathlib import Path

JST = datetime.timezone(datetime.timedelta(hours=9), 'JST')

from libs.mule_xml_analyze import Mule_Xml_Analyze

THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
param_file = "param.yaml"       # パラメータファイル

def main(params):

    date = datetime.datetime.now(JST).strftime('%Y%m%d%H%M')
    prjDir = os.path.abspath(Path().resolve().parents[0])

    #print(prjDir)

    dataDir = prjDir + os.sep + "data"
    outpDir = prjDir + os.sep + "output"
    tmpDir  = prjDir + os.sep + "temp"

    XML_dataDir = dataDir + os.sep + "api"
    XML_outpDir = outpDir + os.sep + date
    os.makedirs(XML_outpDir, exist_ok=True)

    # 処理対象のXMLファイルをリストアップ
    file_items = []
    for root, dirs, files in os.walk(XML_dataDir):
        for file in files:
            file_path = os.path.join(root, file)
            subject, ext = os.path.splitext(os.path.basename(file_path))

            if ext.lower() == '.xml':
                if subject.lower() in params["except_xml"]:
                    pass
                else:
                    fpath_items = file_path.replace(XML_dataDir,"").split(os.sep)
                    #print(fpath_items)
                    #print("-" * 15)

                    # main フォルダを対象。munit を非対象にしたいため。
                    if (not "test" in fpath_items) and (not "target" in fpath_items):
                        file_item = {}
                        file_item["file_path"] = file_path
                        file_item["fname"]     = os.path.basename(file_path)
                        file_item["subject"]   = subject
                        file_item["id_fname"]  = fpath_items[1] + "_" + subject
                        file_item["app_name"]  = fpath_items[1]
                        file_items.append(file_item.copy())

    #pprint.pprint(file_items)

    df_xml_all = pd.DataFrame()

    for file_item in file_items:
        #print(file_item)
        #print("-" * 20)

        file_name = file_item["id_fname"]
        app_name = file_item["app_name"]
        xml_file = file_item["subject"]

        mma = Mule_Xml_Analyze(prjDir, outpDir=XML_outpDir, dataDir=XML_dataDir)
        mma.xml_file_path = file_item["file_path"]

        data_dict = mma.parse_XML_structure()
        mma.get_xml_mule_keys()

        mma.save_dict_data(data_dict, "{}.txt".format(file_name), tmpDir, split = False)

        if mma.dict_flow_enable == True:
            mma.save_dict_data(mma.dict_flow, "{}-flow.txt".format(file_name), tmpDir, split = True)
        
        if mma.dict_sub_flow_enable == True:
            mma.save_dict_data(mma.dict_sub_flow, "{}-subflow.txt".format(file_name), tmpDir, split = True)

        df = mma.find_keys_with_doc_id_and_name(data_dict)
        df["app_name"] = app_name
        df["xml"] = xml_file

        xls_file_name = "{}.xlsx".format(file_name)
        mma.save_to_excel(mma.df_std, xls_file_name)

        _cols = mma.get_cols_std2()
        df_sel = df[_cols].copy()
        df_xml_all = pd.concat([df_xml_all, df_sel], axis=0, ignore_index=True)
        print("-" * 20)

    xls_file_name = "all_mule_project_xml.xlsx"
    mma.save_to_excel(df_xml_all, xls_file_name)


if __name__ == "__main__":

    os.chdir(THIS_FILE_DIR)
    os.chdir("../")
    inpDir = os.getcwd() + os.sep + 'input'
    confPath = os.path.join(inpDir, param_file)
    os.chdir(THIS_FILE_DIR)

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='parameter file path', type=str, default=confPath)

    args = parser.parse_args()

    #print(args.config)
    if os.path.exists(args.config) is False:
        print(args.config + ' is NOT found.')
        sys.exit()

    try:
        with open( args.config, "r", encoding="utf-8") as f:
            params = yaml.load(f,Loader=yaml.FullLoader)

    except Exception as ex:
        print(ex)
        print("### ERROR ###\nyaml file open error.")
        sys.exit()

    main(params)
