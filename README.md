A web-app group project for my Software Engineering course in my Uni, it's not fully completed yet and there are some components missing, but i'll be sure to finish it before the project deadline.

This version is local host only, i use pythonanywhere to host and run it (and of couse i've added a line or two so it can work properly on there, but i'll be sure to tell you which line is it that i change inside app.py).
you can check it out in GlyBirdWho.pythonanywhere.com

Installation is quite simple.
Firstly you need Python3 or higher so you can run it. 
Next up do these steps:
- Install all the of files and to put them in one folder. Make sure the path is something like this
project/
  ├── app.py
  ├── dashboard.db
  ├── requirements.txt
  ├── README.md          <- This one is optional
  └── templates/
      ├── login.html
      ├── register.html
      └── index.html
- Open your terminal
- Go to your file location
- Install the requirements by typing and entering this into your terminal : pip install -r requirements.txt

And you're set, now we just need to run the server. Here's how you do it:
- Open your terminal and go to the file location again
- Type and enter : python app.py
- There should be something showing up
- Copy and paste the link
- You're set, enjoy your new localhost web-app 
