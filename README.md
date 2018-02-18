# Build an Item Catalog Application - Udacity Project 4

This application is designed to allow users to store various football leagues and their corresponding teams. It uses a an object-relational database management system (sqllite) to add, delete, and store the information on each league and team. The application provides a formatted webpage to allow the user to do this on their web browser.

## Installation

There are 5 programs the user must have installed in order to run this file:

1. [Python 2](https://www.python.org)
2. [Virtual Box](https://virtualbox.org)
3. [Vagrant](https://vagrantup.com)
4. [Git](https://git-scm.com/downloads)
5. A web browser of your choice

Instructions to download and install each of these programs can be found in the links above. Git can be replaced with any other command line shell of your preference, but this file explains the process assuming you are using Git Bash.

## Setting up

1. Begin by installing Git, Python 2, Virtual Box, and Vagrant. 
2. Extract the files from catalog.zip and place them in the vagrant directory shared by your virtual machine.

## Virtual Machine

Using Git Bash, launch the Vagrant virtual machine inside the vagrant sub-directory. The command to do this is

`vagrant up`

Then, log into the VM using

`vagrant ssh`
s
If you are requested to enter a password, there is an error in your installation. Use your favourite search engine to troubleshoot this issue.

Assuming you have launched and logged into the VM, switch into the /vagrant directory.

## Google client ID and Secret

Using the Google APIs Console, create a page for the catalog app. This can be done [here](https://console.developers.google.com/apis)
Access your credentials and create an OAuth 2.0 Client ID. Choose web application, and set the authorized JavaScript origins to http://localhost:8000
Download and save the json file (label it clients_secrets.json) in the app directory. 

## Database Setup

A database has been setup, however if you would like to start from scratch, run the database_setup.py file, and populate the database using python or the web interface

## Using the web interface

Run the project.py file from your virtual machine using your command line shell. Open your browser and navigate to localhost:8000. From here, you will see items whcih have already been setup in the database.

In order to edit or add new leagues or teams, you will need to login. Once logged in, you can make edits or deletions to items you previously created. You cannot change items created by other users.

## API Endpoints

1. Show all leagues in JSON - `/leagues/JSON`
2. Show teams in a league in JSON - `/leagues/<int:league_id>/teamsList/JSON`

## Credit

A few points of credit:

1. The code for this application was inspired by a few sources:
	Udacity Full Stack Nanodegree quiz codes (restaurant quiz) as well as forum mentor advisory (particularly from mentor swooding)
2. Formatting leverages [bootstrap 3.11](http://bootstrapdocs.com/v3.1.1/docs/css/) 