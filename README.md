# MLCA: a tool for Machine Learning Life Cycle Assessment

---

MLCA is a tool for assessing the environmental footprint of computation.
It has been described in the ![MLCA paper](https://hal.science/hal-04643414) presented at the 2024 International Conference on ICT for Sustainability (ICT4S) in Stockholm Sweden.

This repository contains the ![code for the tool](https://github.com/blubrom/MLCA/tree/main/boaviztapi) as weel as the ![code and results of all the experiments realised to validate the tool](https://github.com/blubrom/MLCA/blob/main/experiments.org).


## Run the tool

### Prerequisite

Python 3, pipenv recommended

### Setup pipenv

Install pipenv globally

```bash
$ sudo pip3 install pipenv
```

Install dependencies and create a python virtual environment.

```bash
$ pipenv install -d 
$ pipenv shell
```

### Launch a local server

**Once in the pipenv environment**

Development server uses [uvicorn](https://www.uvicorn.org/) and [fastapi](https://fastapi.tiangolo.com/), you can launch development server with the `uvicorn` CLI.

```bash
$ uvicorn boaviztapi.main:app --host=localhost --port 5000
```

### OpenAPI specification (Swagger)

Once API server is launched API swagger is available at [http://localhost:5000/docs](http://localhost:5000/docs). Experiments can be run at this adress.
![The file with the experiments](https://github.com/blubrom/MLCA/blob/main/experiments.org) also detail how to call the tool automatically.

## :scroll: License

GNU Affero General Public License v3.0
