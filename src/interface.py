import json
import os
import re
import requests as r
from datetime import datetime

#? Dependencies that need to be installed using pip install
import inquirer #! (v2.8.0, as of yet no fix for backspace input error)
import iso3166
from getkey import getkey
from yaspin import yaspin 
from yaspin.spinners import Spinners
from rich import print
from rich.console import Console
from rich.text import Text
from rich.traceback import install
from rich.markdown import Markdown
from rich.table import Table

install() # implements custom traceback styling || rich.traceback
console = Console() # creates new rich console || rich.console

isLogedIn = False # global boolean to check if user is logged in

# * Provides styling options for the inquirer list menu
script_dir = os.path.dirname(__file__)
file_path1 = os.path.join(script_dir, 'inqTheme.json') 
f = open(file_path1)
theme_data = json.load(f)
customInq = inquirer.themes.load_theme_from_dict(theme_data)

# * Import markdown file used in displayInfo()
file_path2 = os.path.join('README.md')
f = open(file_path2, 'r')
md = Markdown(f.read())
f.close()



""" 
[D] DESCRIPTION | requests the url and prints a table of results and saves the results to a file
[I] INPUT       | { url: string containing the url }
"""
def requestURL(url):
  countries = []
  
  # Styling of summary table
  table = Table()
  table.add_column("Code", style="cyan", no_wrap=True)
  table.add_column("Country", style="magenta")
  table.add_column("Status", justify="right", style="blue")
  table.add_column("Description", style="red")

  for c in iso3166.countries_by_alpha2.keys():
    countries.append(c.lower())
  countries.sort()

  if not os.path.exists('responses'):
    os.mkdir('responses')

  # Creating directories for the request response files
  requestTime = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")
  requestPath = os.path.join('responses', requestTime)
  analysisPath = os.path.join(requestPath, 'analysis')
  summaryPath = os.path.join(requestPath, 'summary.txt')
  os.mkdir(requestPath)
  os.mkdir(analysisPath)

  # Loop through all countries while displaying a loading spinner
  counter = 1
  with yaspin(Spinners.earth, text='Loading...', color='yellow') as spinner:
    for c in countries:
      country_full = iso3166.countries_by_alpha2[c.upper()].name
      spinner.text = f'[{counter}/{len(countries)}]  Loading ' + c.upper() + '...'

      data_dict = r.runCountry(url, c)
      status_code = data_dict['status_code']

      if data_dict['status_code'] == 200:
        table.add_row(c.upper(), country_full, f"{status_code} ✅")
      else:
        description = data_dict['text']
        table.add_row(c.upper(), country_full, f"{status_code} ❌", description)

      countryPath = os.path.join(analysisPath, f"{country_full}.json")
      with open(countryPath, "w") as outfile:
        json.dump(data_dict, outfile)

      counter+=1
    spinner.stop()
  
  with open(summaryPath, 'w') as w:
    try:
      w.write(print(table, file=w))
    except TypeError as e:
      pass
  
  console.print(table)

  exitPage()



""" 
[D] DESCRIPTION | displays main menu 
[I] INPUT       | { choices: list of choices to display }
[R] RETURNS     | user's choice
[T] RETURN TYPE | dictionary (e.g. "choice" : "Info")
"""
def displayMenu(choices):
  menu = [
  inquirer.List('choice',
                message="MENU",
                choices=choices,
            ),
  ]
  return inquirer.prompt(menu, theme=customInq)



""" 
[D] DESCRIPTION | displays the request prompt to the user
[R] RETURNS     | user's answers to the url query
[T] RETURN TYPE | dictionary (e.g. "url" : "https://www.google.com")
"""
def displayRequest():
  questions = [
    inquirer.Text('url', message="URL",
    validate=validate_url
    ),
  ]
  answer = inquirer.prompt(questions, theme=customInq)  

  requestURL(answer['url'])



""" 
[D] DESCRIPTION | displays login promt to the user
[R] RETURNS     | user's answers to the 3 queries
[T] RETURN TYPE | dictionary (e.g. "url" : "https://www.google.com")
"""
def displayLogin():
  global isLogedIn

  questions = [
    inquirer.Text('accountID', message="CustomerID"),
    inquirer.Password('password', message="Password"),
  ]
  answer = inquirer.prompt(questions, theme=customInq)  

  with yaspin(text='Logging In...', color='yellow') as spinner:
    if r.validate_user(answer['accountID'], answer['password']):
      isLogedIn = True
      spinner.stop()
    else: 
      spinner.stop()
      exitPage()



""" 
[D] DESCRIPTION | validates the url
[I] INPUT       | { answer: dictionary containing pervious user input } 
                  { current: string that represents user input i.e. url }
[R] RETURNS     | True if input is valid, else raises exception
[T] RETURN TYPE | boolean / exception
"""
def validate_url(answer, current):
  regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

  if not re.match(regex, current):
    raise inquirer.errors.ValidationError("", reason='ERROR: invalid URL format -> expected https://www.example.com')
  
  return True
  


""" 
[D] DESCRIPTION | displays the markdown file with all of the essential information
"""
def displayInfo():
  console.print(md)
  exitPage()
  


""" 
[D] DESCRIPTION | a widget to allow user to exit a page
"""
def exitPage():
  qText = Text('\n\n\nPress Q to return back to the Menu: ')
  qText.stylize("bold blue", 0, 11)
  console.print(qText)

  key = ''
  while key != 'q':
    key = getkey().lower()



"""
[D] DESCRIPTION | main function
"""
if __name__ == '__main__':
  temp = True
  loggedIn = ['Info', 'Run', 'Logout', 'Exit']
  loggedOut = ['Info', 'Login', 'Exit']

  while temp:
    os.system('clear')
    x = loggedIn if isLogedIn else loggedOut
    choice = displayMenu(x)['choice']
    os.system('clear')
    
    match choice:
      case 'Info':
        displayInfo()
      case 'Login':
        displayLogin()
      case 'Logout':
        isLogedIn = False
      case 'Run':
        displayRequest()
      case 'Exit':
        temp = False
