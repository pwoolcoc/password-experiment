(Assumes https, though demo does not use it)

# Flow

* Load login screen in browser. Javascript is required.
* User is presented with standard username / password login form
* User enters username & password and submits form
* Form submission event is caught by javascript
* Hash the password using scrypt
* Generate a signing keypair using NACL, with the password hash from #4
  as the seed
* Sign the username using the private key from the generated keypair

For Registration:

* POST the following items to the server: username, public key from the
  generated keypair, and the signed username
* If the server can successfully retrieve the username by using the
  public key to decrypt the signed username, the user is registered

For Login:

* POST the following items to the server: username, signed username
* If the server can successfully retrieve the username by using the
  user's registered public key to decrypt the signed username, log
  the user in.
