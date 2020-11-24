phones=('899205738' '887474415' '899071311')

for phone in "${phones[@]}"
do
	start "" "C:/Program Files/Git/git-bash.exe" -c "/d/installations/python/python.exe run.py '+359' $phone"
done