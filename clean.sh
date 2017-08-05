find -iname "*.pyc" -type f -delete
find -iname "*.o" -type f -delete
find report/ -iname "*.log" -type f -delete
find report/ -iname "*.out" -type f -delete
find report/ -iname "*.toc" -type f -delete
find report/ -iname "*.snm" -type f -delete
find report/ -iname "*.bbl" -type f -delete
find report/ -iname "*.blg" -type f -delete
find report/ -iname "*.aux" -type f -delete
find report/ -iname "*.nav" -type f -delete
find -iname "*~" -type f -delete
find -iname "transportUpwind-*" -type f -delete
find -iname "isothermalHydrodynamics-*" -type f -delete
rm -r tmp/
find case/ -iname "tmp" -type d -exec rm -r {} +
