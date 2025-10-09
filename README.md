# PDF Downloader

The program excepts the Excel file to have the following rows headers:
- `BRnum`
- `Pdf_URL`

**Features**
- Load MS Excel files
- Download pdf files from URLS
- Handle exceptions and invalid PDF Files
- Multithreaded downloads
- Output a csv file with results
- Configurable concurrent downloaders/file paths
- Detect preciously downloaded file and skipping download
- Gracefull shutdown with CTRL+C interrupt

>> **Note** The program will only download files from URLs using *http* or *https*, *ftp* URLs are skipped.  

## Build
**Setup virtuel environment**
```
>> python -m venv .venv
>> .\.venv\Scripts\Activate.ps1
```
**Install packages**
```
>> pip install -r requirements.txt
```

## Usage

**Help**
```
>> python src/pdfdownloader.py -h
```
**Configure**
The program can either be run either with arguments or with a single config file.
```
in_file: "data/Metadata2006_2016.xlsx" # Input file
out_file: "data/metadata2006.csv"      # Output file
out_pdf_dir: "data/metadata2006"       # Directory for the downloaded pdfs
tasks: 20                              # Concurrent downloads
verbose: True                          # Log verbosity 
```

**Run program with config file**
```
>> python src/pdfdownloader --config config.yml
```

**Run program without config file**
```
>> python src/pdfdownloader --in_file data/file.xlsx
```
The other arguments are optional and has the following default values:  
- `--out_dir <PATH_TO_DIRECTORY>`
- `--out_dir <PATH_TO_DIRECTORY>`