GETTING STARTED
===============

* Download the following files (if all you need is tagging, the second
   archive is not necessary):
    - http://www.ark.cs.cmu.edu/TurboParser/sample_models/english_proj_tagger.tar.gz
    - http://www.ark.cs.cmu.edu/TurboParser/sample_models/english_proj_parser.tar.gz

* Expand them, and place the extract files in the `data` directory


CONFIGURATION
=============

The settings for the server can be found in `settings.py`.
Please ensure the TCP port is not already in use on your machine, and that the path to the models are correct.


START/STOP THE SERVER
=====================

Simply run the following command to start: `./nlpserver start`
To stop: `./nlpserver stop`

If starting the server failed, have a look at the log in `nlpserver.log`.
