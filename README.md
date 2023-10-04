# CS50-final-project
# MOVRAT : A Movies Rating Website

#### Description:
My final project for CS50 is a dynamic website that empowers movie enthusiasts to explore and engage the world of movies. This website enables the user to express their opinions and share their review of certain movies to the community. It aims to become a hub for many users for finding a new movies to watch.

All the features includes:
* Review movies
* Make list of movie to watch later
* See all the information of movie or celeb
* See top movies and celebs

How the website works?\
The flow is simple. The user need to register first by inputting username, password, and confirmation password. If the user already have the account just input  username and password in login page. Then it automatically appear the main page, where you can look the overview of the website such as top movies and top celebs, and several button that user can press that will do something. In this website thes user also can find movies or celebs on movies and celebs page respectively. The main function of this website is to share review of certain movies that the user can do on review page. Lastly, the user can also track or list movie to watch later by pressing "add to watch later button" on every page it appeared.

All the information from the user is stored at database called MOVRAT.db, and use sqlite3 to get, insert, and update the database. To connect database and frontend This program use flask in file called app.py.
