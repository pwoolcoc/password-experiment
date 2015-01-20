document.addEventListener("DOMContentLoaded", function(loaded) {
    var login_form = document.getElementById("login"),
        register_form = document.getElementById("register"),
        create_form = function create_form() {
            var form = document.createElement("form"),
                args = [].slice.call(arguments, 0),
                inputs = args[0],
                url = args[1] || "/login";

            for (var id in inputs) {
                var inp = document.createElement("input"),
                    data = inputs[id];
                attach_input(form, inp, id, data);
            }

            form.setAttribute("action", url);
            form.setAttribute("method", "POST");

            return form;
        },
        on_login = function on_login(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var username_el = login_form.querySelector(".username"),
                password_el = login_form.querySelector(".password"),
                username = username_el.value,
                password = password_el.value,
                data = get_data(username, password),
                signed_username = data.signed_username,
                newform = create_form({ "username": username,
                                        "signed_username": signed_username });

            document.body.appendChild(newform);
            newform.submit();

            return false;
        },
        on_register = function on_register(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var username_el = register_form.querySelector(".username"),
                password_el = register_form.querySelector(".password"),
                username = username_el.value,
                password = password_el.value,
                data = get_data(username, password),
                signed_username = data.signed_username,
                publickey = data.publickey,
                newform = create_form({ "username": username,
                                        "publickey": publickey,
                                        "signed_username": signed_username },
                                      "/register");

            console.log("newform: ", newform);
            document.body.appendChild(newform);
            newform.submit();

            return false;
        };

    login_form.addEventListener("submit", on_login);
    register_form.addEventListener("submit", on_register);
});

function attach_input(form, input, name, value) {
    input.value = value;
    input.setAttribute("name", name);
    input.setAttribute("type", "hidden");
    form.appendChild(input);
}

function sign_username(username_bytes, keypair) {
    return nacl.crypto_sign(username_bytes, keypair.signSk);
}

function hash_password(password) {
    var password_bytes = nacl.encode_utf8(password);
        password_scrypted = scrypt.crypto_scrypt(password_bytes,
                                                 nacl.encode_utf8(""),  /* What would we use for the salt here? We need this to be deterministic... */
                                                 Math.pow(2, 4), /* scrypt paper says to use 2^14, but that froze my browser :-/ */
                                                 8, 1, 32);
    return password_scrypted;
}

function get_data(username, password) {
    var username_bytes = nacl.encode_utf8(username),
        password_scrypted = hash_password(password),
        keypair = nacl.crypto_sign_keypair_from_seed(password_scrypted),
        signed_username = sign_username(username_bytes, keypair);
    return {
        "signed_username": base64EncArr(signed_username),
        "publickey": base64EncArr(keypair.signPk)
    };
}
