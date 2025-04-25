# xml_parse_mulesoft

- Script to parse MuleSoft XML files

## Description

- Analyses XML files using xmltodict and converts data to Dict type.
- Extract the settings for each component of MuleSoft while analysing the Dict type data, summarise the data in a DataFrame and output as an Excel file.

## Test environment

|Item|Overview|
|-|-|
|OS|Windows 11 Pro 64bit|
|python| 3.12.4|

## Required modules

|Module Name|Installation Command|
|-|-|
| xmltodict | python -m pip install xmltodict |

## Parsing folder

- Parse the XML files in the ./data/api folder.
  - Copy the Mule project folder in the workspace folder to the . /data/api folder.


## Execution method

Run at the command prompt.

### Execution examples

```shell
 cd src
 python main.py -i -c c:\temp\input\param.yaml
```

If you want to set it up and run it in param.yaml, the following is OK.

```shell
 cd src
 python main.py
```

### Arguments

|Argument|Description|
|-|-|
|-c|File path where the parameter file (param.yaml) is stored.<br> Initial value=". \input\param.yaml" |

## Parameter file

- File name: param.yaml 

### Example definition

```yaml
except_xml:
  - log4j2
  - log4j2-test
  - application-types
  - pom
```

|parameters||explanation|
|-|-|-|
|except_xml||Files to exclude from parsing.|

