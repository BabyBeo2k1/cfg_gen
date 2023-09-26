# cfg_gen
This repository help python user can extract Java method control-flow graph through [networkx](https://networkx.org/documentation/stable/index.html) python library as well as its application in [this paper](1858996.1859006.pdf)

## Set up


To initiate, get requirement in conda:

```
pip install -r requirement.txt
```

## Create a control-flow graph

To create simple control-flow graph handle such simple branching as if/else, do-while, while, try, etc:

```
from methodCFG import Sunit
java_method="your java method" #your java method
sunit=Sunit(java_method)
cfg=sunit.cfg # extract root node include reference type, method name 
```

Overview of each branching node (under developement)

## Selection unit remove/extract

To generate sunit extraction from java files to java file, input file must not contain class or packages, only 1 method. 
### For quick start:

```
import Hung.extractSunit
input="input_java_file.java"
output="output_java_file.java"
extract(input,output)
```

### For generate sunit extraction from text to text:

```
from methodCFG import Sunit
java_method="your java method" #your java method
sunit=Sunit(java_method)
sunit.composeSunit()
print(sunit.source_code)

```