import pyrebase

config = {
    "apiKey": "AIzaSyC4akyZ1_wdI9TWslSlWbxyOby1SsGs-ks",
    "authDomain": "sigam-auth.firebaseapp.com",
    "databaseURL": "",
    "projectId": "sigam-auth",
    "storageBucket": "sigam-auth.firebasestorage.app",
    "messagingSenderId": "69999632854",
    "appId": "1:69999632854:web:65fe443cecf1c5f64e0477"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
#R1
