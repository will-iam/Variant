find -iname "*.o" -type f -delete 2> /dev/null
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -r
find report/ -iname "*.log" -type f -delete 2> /dev/null
find report/ -iname "*.out" -type f -delete 2> /dev/null
find report/ -iname "*.toc" -type f -delete 2> /dev/null
find report/ -iname "*.snm" -type f -delete 2> /dev/null
find report/ -iname "*.bbl" -type f -delete 2> /dev/null
find report/ -iname "*.blg" -type f -delete 2> /dev/null
find report/ -iname "*.aux" -type f -delete 2> /dev/null
find report/ -iname "*.nav" -type f -delete 2> /dev/null
find -iname "*~" -type f -delete 2> /dev/null
find -iname "*.exec" -type f -delete 2> /dev/null
rm -r tmp/ 2> /dev/null
#find cases/ -iname "tmp" -type d -exec rm -r {} + 2> /dev/null
#python regression.py transportUpwind --clean-compile
#find . -iname 'ref2' -type d -exec rm -r {} +
