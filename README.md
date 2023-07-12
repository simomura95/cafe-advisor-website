# Cafe advisor website
The website idea is to store all cafes inserted from user, along with their zone and some of their characteristics that could be useful to work remotely from there (eg. presence of power socket).

Non-authenticated user can only view the cafes, eventually filtering them.<br>
Registering on the website allows users to add new cafes and review them, in a blog-like fashion.<br>
Only admin users (role granted to everyone on registration for now, to show all website features) can delete or edit cafes.<br>
An avatar image is assigned to each user using Gravatar, based on one's e-mail.

Registration uses Flask-login and hashing is used for the passwords, so the original one is never stored in the database.<br>
Bootstrap is used for all CSS.

The website is pretty simple in its structure, eg. database is created with SQLite and the "cafe location" is just a string, but it contains all features accounted by this project.<br>
Moreover, the same structure could be used to build a fully-fledged blog.
