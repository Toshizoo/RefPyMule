#-*- coding: utf-8 -*-

import codecs
import gc
import json
import os
import pandas as pd
import re
import xmltodict
from collections.abc import MutableMapping

gc.enable()

class Mule_Xml_Analyze():

    __COLS_STD = [
        'doc_id',
        'flow',
        'doc_name',
        'component',
        'dict_value',
        'param_0',
        'param_1',
        'http:body',
        'http:headers',
        'http:query-params',
        'http:uri-params',
        '@method',
        '@url',
        '@path',
        '@sendCorrelationId'
    ]

    __COLS_STD2 = [
        'app_name',
        'xml',
        'doc_id',
        'flow',
        'doc_name',
        'component',
        'dict_value',
        'param_0',
        'param_1',
        'http:body',
        'http:headers',
        'http:query-params',
        'http:uri-params',
        '@method',
        '@url',
        '@path',
        '@sendCorrelationId'
    ]

    __COLS_MINI = [
        'doc_id',
        'flow',
        'doc_name',
        'component',
        'dict_value',
        'param_0',
        'param_1'
    ]

    def __init__(self, prjDir, outpDir=None, dataDir=None):

        self.inpDir = prjDir + os.sep + "input"
        self.tmpDir = prjDir + os.sep + "temp"

        if dataDir is None:
            self.datDir = prjDir + os.sep + "data"
        else:
            self.datDir = dataDir

        if outpDir is None:
            self.outpDir = prjDir + os.sep + "output"
        else:
            self.outpDir = outpDir

        self.xml_file_path = None
        self.xml_dict = None
        self.xml_dict_keys = None

        self.dict_flow_enable = False
        self.dict_sub_flow_enable = False

        self.df = pd.DataFrame()
        self.df_all = pd.DataFrame()
        self.df_std = pd.DataFrame()
        self.df_http = pd.DataFrame()

    def get_cols_std2( self ):
        return self.__COLS_STD2

    def set_file_path(self, fname):
        #self.xml_file_path = os.path.join(self.inpDir, fname)
        self.xml_file_path = os.path.join(self.datDir, fname)
        return self.xml_file_path

    def save_to_excel(self, df, xls_file_name):
        save_fpath = os.path.join(self.outpDir, xls_file_name)
        df.to_excel( save_fpath, index=True)
        print(" * ", save_fpath)

    def save_dict_data(self, data_dict, save_fname, save_path=None, split = False):

        if save_path == None:
            save_path = self.outpDir
        if(split == True):
            if isinstance(data_dict, dict):
                if "@name" in data_dict.keys():
                    head_lines = "========================================\n{}\n========================================\n\n".format(data_dict["@name"])
                    json_lines = json.dumps(data_dict, indent=4).splitlines()
                    out_text = head_lines + "\n".join(json_lines)

            elif isinstance(data_dict, list):
                out_txt = []
                for _dict in data_dict:
                    if "@name" in _dict.keys():
                        head_lines = "========================================\n{}\n========================================\n\n".format(_dict["@name"])
                        json_lines = json.dumps(_dict, indent=4).splitlines()
                        flow_line = head_lines + "\n".join(json_lines)
                        out_txt.append(flow_line)

                out_text = "\n".join(out_txt)

        else:
            json_lines = json.dumps(data_dict, indent=4).splitlines()
            out_text = "\n".join(json_lines)
        
        save_fpath = os.path.join(save_path, save_fname)
        codecs.open(save_fpath, "w", encoding="utf-8").write(out_text)
        print(" * ", save_fpath)


    # XMLの構造を解析
    def parse_XML_structure(self,file_path = None):

        if file_path == None:
            file_path = self.xml_file_path

        print(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            xml_data = f.read()
            try:
                data_dict = xmltodict.parse(xml_data)
                self.xml_dict = data_dict                  # Addition
                self.set_xml_mule_keys()
                self.set_xml_dict_mule()
                return data_dict
            except Exception as e:
                print(f"Error parsing XML: {e}")
                return None

    def set_xml_mule_keys(self):
        self.xml_dict_mule_keys = self.xml_dict['mule'].keys()

    def get_xml_mule_keys(self):
        return list(self.xml_dict_mule_keys)

    def set_xml_dict_mule(self):
        self.dict_mule = self.xml_dict['mule']
        self.dict_flow_enable = False
        self.dict_sub_flow_enable = False

        try:
            self.dict_flow = self.xml_dict['mule']['flow']
            self.dict_flow_enable = True
            print("set data : mule-'flow'")
        except:
            print("Mule Flow is None.")
            self.dict_flow = {}
            self.dict_flow_enable = False

        try:
            self.dict_sub_flow = self.xml_dict['mule']['sub-flow']
            self.dict_sub_flow_enable = True
            print("set data : mule-'sub-flow'")
        except:
            print("Mule sub-flow is None.")
            self.dict_sub_flow = {}
            self.dict_sub_flow_enable = False

    def set_analytic_object(self, analytic_xml):
        self.analytic_xml = analytic_xml

    def set_refinement_object(self, refinement_xml):
        self.refinement_xml = refinement_xml


    def find_keys_with_doc_id_and_name(self, data_dict):

        keys_with_both_1 = []
        keys_with_both_2 = []
        doc_names = []
        doc_ids = []

        def _recursive_search(data, current_path_1="", current_path_2=""):
            if isinstance(data, dict):
                has_name = False
                has_id = False
                has_apikit = False
                get_name = ""
                get_id = ""
                get_apikit = ""
                for key, value in data.items():
                    new_path_1 = current_path_1 + "." + key if current_path_1 else key
                    new_path_2 = current_path_2 + "." + key if current_path_2 else key
                    if key == "@doc:name":
                        has_name = True
                        get_name = value
                    elif key == "@doc:id":
                        has_id = True
                        get_id = value
                    elif key in ["@config-ref","@type"]:
                        has_apikit = True
                        get_apikit = key

                    elif isinstance(value, dict) or isinstance(value, list):
                        _recursive_search(value, new_path_1, new_path_2)
                if has_name and has_id:
                    #print("{} <tab> {} <tab> {}".format(get_id,get_name,current_path))
                    doc_names.append(get_name)
                    doc_ids.append(get_id)
                    keys_with_both_1.append(current_path_1)
                    keys_with_both_2.append(current_path_2)
                elif (has_apikit == True) and (has_id == False) and (has_name == False):
                    doc_names.append(get_apikit)
                    doc_ids.append("_API_KIT")
                    keys_with_both_1.append(current_path_1)
                    keys_with_both_2.append(current_path_2)

                elif (has_id == False) and (has_name == False):
                    _name = current_path_1.split(".")[-1]
                    if _name in ["http:listener-config", "apikit:config"]:
                        doc_names.append(_name)
                        doc_ids.append("_API_Global")
                        keys_with_both_1.append(current_path_1)
                        keys_with_both_2.append(current_path_2)


            elif isinstance(data, list):
                for i, item in enumerate(data):
                    #_recursive_search(item, current_path + f"[{i}]")
                    _recursive_search(item, current_path_1 + f".{i}", current_path_2 + f"[{i}]")


        _recursive_search(data_dict)
        
        df = pd.DataFrame()
        df["doc_id"] = doc_ids
        df["dict_key"] = keys_with_both_1
        df["key_sub"] = keys_with_both_2

        df["flow"] = df["key_sub"].apply(lambda x: x.split(".")[1])
        df["doc_name"] = doc_names
        df["component"] = df["key_sub"].apply(lambda x: re.sub(r"\[\d+\]", "", x.split(".")[-1]) )
        df["dict_value"]= df["dict_key"].apply(lambda x: self.get_dict_key_value(data_dict, x) )
        df["dict_value_raw"]= df["dict_key"].apply(lambda x: self.get_dict_key_value_raw(data_dict, x) )
        
        df["param_0"]  = df.apply( lambda x: self.extract_value_dict_data(x["component"], x["dict_value_raw"], 0), axis=1 )
        df["param_1"]  = df.apply( lambda x: self.extract_value_dict_data(x["component"], x["dict_value_raw"], 1), axis=1 )
        df["http:body"]          = df.apply( lambda x: self.extract_value_dict_data(x["component"], x["dict_value_raw"], 2), axis=1 )
        df["http:headers"]       = df.apply( lambda x: self.extract_value_dict_data(x["component"], x["dict_value_raw"], 3), axis=1 )
        df["http:query-params"]  = df.apply( lambda x: self.extract_value_dict_data(x["component"], x["dict_value_raw"], 4), axis=1 )
        df["http:uri-params"]    = df.apply( lambda x: self.extract_value_dict_data(x["component"], x["dict_value_raw"], 5), axis=1 )
        df["@method"]            = df.apply( lambda x: self.extract_value_dict_data(x["component"], x["dict_value_raw"], 6), axis=1 )
        df["@url"]               = df.apply( lambda x: self.extract_value_dict_data(x["component"], x["dict_value_raw"], 7), axis=1 )
        df["@path"]              = df.apply( lambda x: self.extract_value_dict_data(x["component"], x["dict_value_raw"], 8), axis=1 )
        df["@sendCorrelationId"] = df.apply( lambda x: self.extract_value_dict_data(x["component"], x["dict_value_raw"], 9), axis=1 )


        self.df_all = df.copy()

        _cols = self.__COLS_STD
        self.df_std = df[_cols].copy()

        _cols = self.__COLS_MINI
        self.df_mini = df[_cols].copy()

        return df

    def get_dict_key_value(self, refine_dict, inp_keys):

        keys_list = inp_keys.split(".")
        keys_list = [int(x) if x.isdigit() else x for x in keys_list]

        for key in keys_list:
            refine_dict = refine_dict[key]

        return json.dumps(refine_dict, indent=4)

    def get_dict_key_value_raw(self, refine_dict, inp_keys):

        keys_list = inp_keys.split(".")
        keys_list = [int(x) if x.isdigit() else x for x in keys_list]

        for key in keys_list:
            refine_dict = refine_dict[key]
                
        return refine_dict


    def extract_value_dict_data(self, component, dict_value, sel):

        #dict_value = json.loads(str_value)
        value = ["*" for x in range(10)] 

        if (component == "logger"):
            if "@message" in dict_value.keys():
                value[0] = dict_value["@message"].replace("\t","    ")

        elif(component == "ee:transform"):
            if "ee:message" in dict_value.keys():
                try:
                    value[0] = dict_value["ee:message"]["ee:set-payload"].replace("\t","    ")
                except:
                    value[0] = dict_value["ee:message"]
                    #pass

            if "ee:variables" in dict_value.keys():
                #value[1] = dict_value["ee:variables"]["ee:set-variable"]
                try:
                    get_values = dict_value["ee:variables"]["ee:set-variable"]
                except:
                    get_values = ""

                if isinstance(get_values, dict):
                    #value[1] = get_values
                    for _key, _value in get_values.items():
                        if _key == "#text":
                            value[2] = _value.replace("\t","    ")
                        elif _key == "@resource":
                            value[2] = _value
                        elif _key == "@variableName":
                            value[1] = _value
 
                    
                elif isinstance(get_values, list):
                    values_list = []
                    #value[1] = dict_value["ee:variables"]["ee:set-variable"]
                    n = 1
                    for get_value in get_values:
                        n = n + 1
                        for _key, _value in get_value.items():
                            if _key == "#text":
                                value[n] = _value.replace("\t","    ")
                            elif _key == "@resource":
                                value[n] = _value
                            elif _key == "@variableName":
                                values_list.append(_value)
                    
                    value[1] = "\n".join(values_list)


        elif(component == "set-payload"):
            value[0] = dict_value.get('@value', "*").replace("\t","    ")

        elif(component == "set-variable"):
            if "@value" in dict_value.keys():
                value[0]= dict_value["@value"].replace("\t","    ")
            if "@variableName" in dict_value.keys():
                value[1] = dict_value["@variableName"]

        elif(component == "choice"):
            if "when" in dict_value.keys():
                try:
                    value[0] = dict_value["when"]["@expression"]
                except:
                    pass

        elif(component == "foreach"):
            if "@collection" in dict_value.keys():
                try:
                    value[0] = dict_value["@collection"]
                except:
                    pass

        elif(component == "http:request"):
            value[0] = dict_value.get('@config-ref', "*")
            value[1] = dict_value.get('@target', "*")
            value[2] = dict_value.get('http:body', "*").replace("\t","    ")
            value[3] = dict_value.get('http:headers', "*").replace("\t","    ")
            value[4] = dict_value.get('http:query-params', "*").replace("\t","    ")
            value[5] = dict_value.get('http:uri-params', "*").replace("\t","    ")
            value[6] = dict_value.get('@method', "*")
            value[7] = dict_value.get('@url', "*")
            value[8] = dict_value.get('@path', "*")
            value[9] = dict_value.get('@sendCorrelationId', "*")

        elif(component == "on-error-continue"):
            if "@type" in dict_value.keys():
                value[0] = dict_value["@type"]
            if "@enableNotifications" in dict_value.keys():
                value[1] = dict_value["@enableNotifications"]
            if "@logException" in dict_value.keys():
                value[2] = dict_value["@logException"]

        elif(component == "until-successful"):
            value[0] = dict_value.get('@maxRetries', "*")
            value[1] = dict_value.get('@millisBetweenRetries', "*")

        elif(component == "http:request-config"):
            value[0] = dict_value.get('http:request-connection', {}).get('http:client-socket-properties', {}).get('sockets:tcp-client-socket-properties', {}).get('@connectionTimeout', "*")
            value[1] = dict_value.get('@responseTimeout', "*")
            value[2] = dict_value.get('http:request-connection', {}).get('@connectionIdleTimeout', "*")
            value[3] = dict_value.get('http:request-connection', {}).get('@protocol', "*")
            value[4] = dict_value.get('http:request-connection', {}).get('@host', "*")
            value[5] = dict_value.get('http:request-connection', {}).get('@port', "*")
            value[6] = dict_value.get('@basePath', "*")

        elif(component == "http:listener-config"):
            value[0] = dict_value.get('http:listener-connection', {}).get('@connectionIdleTimeout',"*")
            value[1] = dict_value.get('http:listener-connection', {}).get('@readTimeout', "*")

            value[3] = dict_value.get('http:listener-connection', {}).get('@protocol', "*")
            value[4] = dict_value.get('http:listener-connection', {}).get('@host', "*")
            value[5] = dict_value.get('http:listener-connection', {}).get('@port', "*")
            value[6] = dict_value.get('@basePath', "*")

        elif(component == "sftp:config"):
            value[0] = dict_value.get('sftp:connection', {}).get('@connectionTimeout', "*")
            value[1] = dict_value.get('sftp:connection', {}).get('@connectionTimeoutUnit', "*")
            value[2] = dict_value.get('sftp:connection', {}).get('@responseTimeout', "*")
            value[3] = dict_value.get('sftp:connection', {}).get('@responseTimeoutUnit', "*")
            value[4] = dict_value.get('expiration-policy', {}).get('@maxIdleTime', "*")
            value[5] = dict_value.get('expiration-policy', {}).get('@timeUnit', "*")

        elif(component == "sftp:rename"):
            value[0] = dict_value.get('@config-ref', "*")
            value[1] = dict_value.get('@path', "*")
            value[2] = dict_value.get('@to', "*")
            value[3] = dict_value.get('@overwrite', "*")

        elif(component == "sftp:write"):
            value[0] = dict_value.get('@config-ref', "*")
            value[1] = dict_value.get('@path', "*")
            value[2] = dict_value.get('sftp:content', "*")

        elif(component == "sftp:read"):
            value[0] = dict_value.get('@config-ref', "*")
            value[1] = dict_value.get('@path', "*")


        #elif(component == ""):
        #    value[0] = dict_value.get('', "*")
        #    value[1] = dict_value.get('', "*")
        # NG
        # ret_value = value[sel].replace("\t", "    ")

        #return json.dumps(value[sel], indent=4)
        ret_value = value[sel]
        return ret_value


