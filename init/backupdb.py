import os
command = 'export PGPASSWORD=C8kdcUrAQy66U\npg_dump -U alexandre -h localhost gargandb| gzip > %s' % "mysqldump.db"
os.system(command)
