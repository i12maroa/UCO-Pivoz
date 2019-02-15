

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        let cookies = document.cookie.split(';');
        for (let i = 0; i<cookies.length; i++) {
            let cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring( name.length + 1));
                break;
            }
        }
        console.log('CSRF_TOKEN = ' + cookieValue);
    } return cookieValue;
}

function makeLink() {
    recorder && recorder.exportWAV(function (blob) {
        let fd = new FormData();
        let obj = "";
        pk_obj = [];
        fd.append("audio", blob, "speech");
        let csrftoken = getCookie('csrftoken');
        let xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
            if (this.readyState === 4 && this.status === 200) {
                obj = JSON.parse(this.responseText);
                console.log("JSON response:" + JSON.stringify(obj) + ". JSON lenght: " + obj.length);
                pk_obj.push();
                console.log("El valos de obj es: " + JSON.stringify(obj));
                if (obj['error']){
                    showError(obj['error']);
                }
                else if (obj['comando']){
                    switch (obj['comando']) {
                        case "ver":
                            console.log("El usuario quiere ver las imagenes");
                            if (!$('#lightbox-modal').is(":visible")){
                                verImagen();
                                showInfo(obj[0]['speech']);
                            }
                            break;

                        case "siguiente":
                            console.log("Siguiente Imagen");
                            siguienteImagen();
                            showInfo("Comando: Siguiente");
                            break;

                        case "anterior":
                            console.log("Imagen anterior");
                            anteriorImagen();
                            break;

                        case "salir":
                            console.log("Salir");
                            if ($('#lightbox-modal').is(":visible")){
                                $('#lightbox-modal').remove();
                                $('div.modal-backdrop').remove();
                                $('body').removeClass('modal-open');
                            }
                            break;

                        case "volumeUp":
                            // TODO: Implementar subir volumen de videos
                            var volume = $('video.focus').prop('volume');
                            console.log("Volumen: " + volume)
                            var newVolume = volume + 0.1;
                            $('video.focus').prop('volume',newVolume);
                            break;

                        case "VolumeDown":
                            // TODO: Implementar bajar volumen de videos
                            break;

                        case "pause":
                            // TODO: Implementar pausa de videos
                            break;

                        case "play":
                            // TODO: Implementar play
                            break;
                        case "menu":
                            window.location.replace("http://127.0.0.1:8000/");
                            console.log("Menu principal intento entrar");
                            break;
                    }


                }
                else {
                    showInfo(obj[0]['speech']);
                    addFilterImages(obj);                               //Añadimos las imagenes filtradas al documento

                    focusImage($('img.img-responsive:first'));           // Hacemos foco en la primera imagen de todas.
                    focusImage($('video:first'));

                }
            }
        };
        xhr.open('POST', uploadAudio_url , true);
        //alert(uploadAudio_url)
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
        /*xhr.onload = addFilterImages(obj);*/
        xhr.onload = function () {
        };
        xhr.onerror = function (e) {
            console.log("Error Uploading audio" + e)
        };

        xhr.send(fd);
    });
}

function focusImage(image) {
    image.addClass('focus');
}

function siguienteImagen() {
    let current = 0;
    let imagelist = $('a[data-lightbox]').each(function (index) {
        if ($(this).children(":first-child").hasClass('focus')){
            current = index;
        }
    });
    // if (current == imagelist.length - 1) {current = -1};
    // focusImage($(imagelist).eq(current+1));
    // lightBox($(imagelist).eq(current+1).parent(), 'click');
    if (imagelist.length != 1) {                                        // En caso de que solo haya una imagen, no nos movemos.
        $(imagelist).eq(current).children(":first-child").removeClass('focus pulse');
        if (current == imagelist.length - 1) { current = -1 };          // En caso de ser la ultima imagen. La siguiente sera la primera
        $(imagelist).eq(current+1).children(":first-child").addClass('focus pulse');
        slide($(imagelist).eq(current), "next");
        console.log("Muchas Imagenes");
    }else {
        console.log("Una imagen");
    }
    //alert('Current: ' + current +'. Length: ' + imagelist.length);
}

function anteriorImagen(){
    let current = 0;
    let imagelist = $('img.img-responsive').each(function (index) {
        if ($(this).hasClass('focus')) {
            current = index;
        }
    });
    if (imagelist.length != 1) {                                              // En caso de que solo haya una imagen, no nos movemos.
        $(imagelist).eq(current).removeClass('focus pulse');
        if (current == 0) {
            current = imagelist.length;
        };
        $(imagelist).eq(current - 1).addClass('focus pulse');
        slide($(imagelist).eq(current).parent(), "previous");
        console.log("Muchas Imagenes");
    }else {
        console.log("Una imagen");
    }
}

function verImagen() {
    let video = $('video');
    if (video.hasClass('focus')){
        lightBox(video);
    }
    else{
        let image = $('img.focus').parent();
        lightBox(image, 'click');
    }

}

function showInfo(info) {
    let popUp = document.getElementById("infoBalloon");
    while (popUp.firstChild) {
        popUp.removeChild(popUp.firstChild);
    }
    let elInfo = document.createElement("p");
    elInfo.innerHTML = info;
    popUp.appendChild(elInfo);
    popUp.style.visibility = "visible";
    popUp.style.display = "block";
    popUp.style.backgroundColor = 'rgba(53,159,28,0.41)';
    $(popUp).fadeOut(8000);
}

function showError(error) {
    let popUp = document.getElementById("infoBalloon");
    while (popUp.firstChild) {
        popUp.removeChild(popUp.firstChild);
    }
    let elerror = document.createElement("h4");
    elerror.innerHTML = error;
    let elText = document.createElement("p");
    elText.innerHTML = 'Prueba a decir: </br> <strong> Ver todas las fotos </strong>';
    popUp.appendChild(elerror);
    popUp.appendChild(elText);
    popUp.style.visibility = "visible";
    popUp.style.display = "block";
    $(popUp).fadeOut(8000);
}

function addFilterImages(objects) {

    let elImgGrid = document.getElementById("imageGridAll");

    console.log("Resultado: " + objects + ". Nº de elementos: " + objects.length);

    //Si hay objetos en la consulta, eliminamos las imagenes del grid principal para mostrar las de la nueva consulta.
    while (elImgGrid.firstChild) {
        elImgGrid.removeChild(elImgGrid.firstChild);
    }

    // Recorremos el JSON para mostrar las fotos en el grid
    for (var i = 0; i < objects.length; i++) {
        let elDiv = document.createElement("div");
        let elTitle = document.createElement("h3");
        elTitle.className = "mg-md tc-mint-cream";
        elTitle.textContent = objects[i].titulo;
        let elKey = document.createElement("p");
        let elA = document.createElement("a");
        elA.href = "#";
        elA.dataset.caption = objects[i].titulo;
        elA.dataset.lightbox = objects[i].src;
        elA.dataset.galleryId = "gallery-1";
        elKey.textContent = objects[i].keywords;
        if (objects[i]['type'] == "imagen"){
            $('h2.tc-honeydew').text("Galería de fotos");
            elDiv.className = "col-sm-2";
            let elImg = document.createElement("img");
            elImg.src = objects[i].src;
            elImg.dataset.src = objects[i].thumbnail;
            elImg.className ="img-responsive lazyload pulse-hvr animated";
            elA.appendChild(elImg);
        }
        else if (objects[i]['type'] == "video")
        {
            $('h2.tc-honeydew').text("Videoteca");
            elDiv.className = "col-sm-3";
            let videoContainer = document.createElement("div");
            videoContainer.className = "embed-responsive embed-responsive-16by9 animated swing-hvr";
            let elVid = document.createElement("video");
            elVid.controls = "controls";
            elVid.className = "embed-responsive-item lazyload";
            elVid.autoplay = "";
            elVid.dataset.src = objects[i].src;
            elVid.dataset.lightbox = objects[i].src;
            elVid.src = objects[i].src;
            elVid.textContent = "Your browser does not support HTML5 video.";
            elA.dataset.autoplay = 1;
            videoContainer.appendChild(elVid);
            elA.appendChild(videoContainer);
        }
        elDiv.appendChild(elA);
        elDiv.appendChild(elTitle);
        elDiv.appendChild(elKey);
        elImgGrid.appendChild(elDiv);
    }
}