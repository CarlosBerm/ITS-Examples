# examples
A collection of code examples you can use to access the U-M GPT Toolkit API service.  

**Common required parameters**  
  
Note that these parameters may be represented by slightly different naming conventions, depepending on script language and module requirements.  

model #model name - available models can be accessed by running the get_models.py file in the Python folder.
API gateway URL #API endpoint
API_KEY #your API key  

Please create a package.json file in the same directory as your script with the following:

{
  "type": "module",
  "dependencies": {
    "openai": "^4.20.1"
  }
}