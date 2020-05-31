# Léodagan

Léodagan aims to be the next davenull, and be a nétiquette checker, written in
Python 3.

# Usage

```
./leodagan.py -h # get help
./leodagan <file> # check the nétiquette on file
./leodagan -q <file> # quiet output, errors only. Useful for scripts
```

## Verbosity

By default Léodagan prints some (not so) useful information, with the date
and error level. Some CLI switches are available to change such behavior.

- `-v, -vv, -vvv, -vvvv` : Increase verbosity and debug option. The more you add, the more verbose Léodagan is
- `-q` : Suppress many informations from the output, and prints only the nétiquette mismatchs found. Used to generate a report that may be given to students
- `--list-success, --list-fail` : Only list `From` header and such minimalistic information. See the appropriate chapter dedicated to those options

## List only the people who respected (or not) the nétiquette

To list all the respectfully people:
```
./leodagan.py <files> --list-success --process-all-files
```
Errors are printed to stderr

Add `-v` to get the path of the news considered. As usual, you can stack up
`-v` to increase verbosity

The opposite flag, `--list-fail`, behaves the same

# Author

Written by Cyril `zarak` Duval - cyril@cri.epita.fr

# License

`cat LICENSE`
