[app]

# (str) Title of your application
title = Zaraflow

# (str) Package name
package.name = zaraflow

# (str) Package domain (needed for android packaging)
package.domain = org.zaraflow

# (str) Source directory where the application files are located
source.dir = .

# (list) Source files to include (let it empty to include all files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning
version = 0.1

# (list) Application requirements
requirements = python3,kivy==2.3.1,plyer

# (str) Supported orientations
orientation = portrait

# (list) Permissions
android.permissions = INTERNET