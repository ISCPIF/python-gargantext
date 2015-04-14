
for tbl in `psql -qAt -c "select tablename from pg_tables where schemaname = 'public';" gargandb` ; do  
  psql -c "alter table $tbl owner to gargantua" gargandb ; 
done
