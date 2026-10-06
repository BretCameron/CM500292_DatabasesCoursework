# Flight Management Database

CM500292 Databases coursework: a Python command line app using SQLite for an interstellar airline's flights, pilots and destinations.

## Run it

Python 3.12, standard library only.

```sh
python main.py               # run the app
python setup_db.py --reset   # restore the sample data
```

Choose an option by number, or `0` to exit.

## Layout

| Where          | What                                                  |
| -------------- | ----------------------------------------------------- |
| `setup_db.py`  | Schema, indexes, triggers and sample data             |
| `db.py`        | Database connection                                   |
| `tables/`      | All SQL queries, one class per table                  |
| `models.py`    | Row types returned by the queries                     |
| `main.py`      | The menu                                              |
| `controllers/` | Menu actions: prompt, run the query, print the result |
| `rules.py`     | Validation the schema cannot express                  |
| `utils/`       | Input prompts and result tables                       |
