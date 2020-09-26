# mtn-huts Overview over mountain huts in Switzerland.



= Initial Steps

Got into your workdir:

  cd ~/.../mtn-huts

Create a virtual environment:

  python3 -m venv env

Activate virtual enviroment:

  source env/bin/activate


Install requirements:

  pip install -r main/requirements.txt

Deactivate environment:

  deactivate


= Commands

In order to run your scripts you need to active the virtual enviroment for this project.
If not created yet follow the initial steps, if installed already you need todo the following
two steps:

  cd ~/.../mtn-huts
  source env/bin/activate

== Deploy

  gcloud app deploy --project mtn-huts main/ 


