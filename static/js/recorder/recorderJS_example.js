var audio_context;
var recorder;
var pk_obj = [];

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != "") {
        var cookies = document.cookie.split(';');
        for (var i = 0; i<cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1)== (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring( name.length + 1));
                break;
            }
        }
        console.log('CSRF_TOKEN = ' + cookieValue);
    } return cookieValue;
}
//Creación del stream de audio
function startUserMedia(stream){
    var input = audio_context.createMediaStreamSource(stream);
    /*__log('Media stream created.');*/
    //Inicializamos el recorder y le pasamos el stream de audio que creamos previamente para que lo use para grabar
    recorder = new Recorder(input);
    detecteSilence(stream, onSilence, onSpeak, 500, -50);
    /*__log('Recorder initialised');*/
}

/*function __log(e, data){
    log.innerHTML += "\n" + e + " " + (data || '') + "<br/>";
}*/

function startRecording(button) {
    audio_context.resume();
    recorder && recorder.record();
    //Desactivamos el boton de emepezar a grabar y activamos el de parar
    /*button.disabled = true;
    button.nextElementSibling.disabled = false;*/
    // __log('Recording...');
    console.log("Start");
    console.log(recorder.recording);
};

function stopRecording(button) {
    recorder && recorder.stop();
    /*button.disabled = true;
    button.previousElementSibling.disabled = false;*/
    // __log("Stopped Recording");
    console.log("Stop:");
    console.log(recorder.recording);
    //Enviamos el audio
    makeLink();

    recorder.clear();
    // get_image_speech();
    // uploadAudioForm();

}

function detecteSilence(stream, onSoundEnd = _=>{}, onSoundStart = _=>{}, silence_delay = 500, min_decibels = 50) {
    const AudioContext = window.AudioContext // Default
    || window.webkitAudioContext // Safari and old versions of Chrome
    || false;
    const ctx = new AudioContext;
    const analyser = ctx.createAnalyser();
    const streamNode = ctx.createMediaStreamSource(stream);
    streamNode.connect(analyser);
    analyser.minDecibels = min_decibels;

    const data = new Uint8Array(analyser.frequencyBinCount); // will hold our data
    let silence_start = performance.now();
    let triggered = false; // trigger only once per silence event

    function loop(time) {
        requestAnimationFrame(loop); // we'll loop every 60th of a second to check
        analyser.getByteFrequencyData(data); // get current data
        if (data.some(v => v)) { // if there is data above the given db limit
            if(triggered){
                triggered = false;
                onSoundStart();
            }
            silence_start = time; // set it to now
        }
        if (!triggered && time - silence_start > silence_delay) {
            onSoundEnd();
            triggered = true;
        }
    }
    loop();
}

// Activación por voz
function onSilence() {
    stopRecording();
    $('#micBtn').removeClass("cmn-t-pulse");

}
function onSpeak() {
    startRecording();
    $('#micBtn').addClass("cmn-t-pulse");
}

// Activación manual del micro, en caso de desactivar activación por voz
function startButton(btn) {
    if (recorder.recording == false) {
        startRecording(btn);
        $('#micBtn').addClass("cmn-t-pulse");

    }
    else {
        stopRecording(btn);
        $('#micBtn').removeClass("cmn-t-pulse");
    }

}



function makeLink() {
    recorder && recorder.exportWAV(function (blob) {
        /*let fd = new FormData(document.getElementById("AudioUploadForm"));*/
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
                pk_obj.push()
                /*for(var i = 0; i < obj.length; i++) {
                    if(obj.length === 1){
                        pk_obj.push('[ {"titulo": "' + obj[i]['titulo']  +
                            '", "src": "' + obj[i]['src'] +
                            '", "thumb": "' + obj[i]['thumbnail'] + '"}]');
                    }
                    else if (i===0){
                        pk_obj.push('[ {"titulo": "' + obj[i]['titulo']  + '", "src": "' + obj[i]['src'] + '", "thumb": "' + obj[i]['thumbnail'] + '"}');
                    } else if (i===obj.length-1){
                        pk_obj.push('{"titulo": "' + obj[i]['titulo']  + '", "src": "' + obj[i]['src'] + '", "thumb": "' + obj[i]['thumbnail'] + '"}]');
                    } else {
                        pk_obj.push('{"titulo": "' + obj[i]['titulo']  + '", "src": "' + obj[i]['src'] + '", "thumb": "' + obj[i]['thumbnail'] + '"}');
                    }
                }
                console.log("Result: " + pk_obj);*/
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
                            showInfo("Comando: Anterior");
                            anteriorImagen();
                            break;

                        case "salir":
                            if ($('#lightbox-modal').is(":visible")){
                                showInfo("Comando: Salir");
                                $('#lightbox-modal').remove();
                                $('div.modal-backdrop').remove();
                                $('body').removeClass('modal-open');
                            }
                            break;

                        case "volumeUp":
                            var video = $('#lightbox-video-container').find('video');
                            if (video.length != 0 && !video.paused){
                                let volume = video.prop('volume');
                                let newVolume = volume + 0.2;
                                video.prop('volume',newVolume);
                            }
                            else {
                                showError("Actualmente no hay ningún video en reproducción.")
                            }
                            break;

                        case "volumeDown":
                            var video = $('#lightbox-video-container').find('video');
                            if (video.length != 0 && !video.paused){
                                let volume = video.prop('volume');
                                let newVolume = volume - 0.2;
                                video.prop('volume',newVolume);
                            }
                            else {
                                showError("Actualmente no hay ningún video en reproducción.")
                            }
                            break;

                        case "pausa":
                            var video = $('#lightbox-video-container').find('video');
                            if (video.length != 0 && !video.get(0).paused){
                                showInfo(obj['speech']);
                                $('#lightbox-video-container').find('video').get(0).pause();
                            }

                            break;

                        case "play":
                            console.log("Entra play");
                            var video = $('#lightbox-video-container').find('video');
                            if (video.length != 0 && video.get(0).paused){
                                showInfo(obj['speech']);
                                $('#lightbox-video-container').find('video').get(0).play();
                            }
                            break;
                        case "menu":
                            if (!$('#lightbox-modal').is(":visible")){
                                showInfo(obj['speech']);
                                setTimeout(function () {
                                    window.location.replace(urlIndex);
                                }, 2000);

                            }
                            break;

                        case "menu-fotos":
                            if (window.location.pathname == urlIndex ){
                                showInfo(obj['speech']);
                                window.location.replace(urlImages);
                            }
                            // else{
                            //     showError("Antes debes de ir al menú principal");
                            // }
                            break;

                        case "menu-videos":
                            if (window.location.pathname == urlIndex ){
                                showInfo(obj['speech']);
                                window.location.replace(urlVideos);
                            }
                            break;

                        case "menu-albums":
                            if (window.location.pathname == urlIndex ) {
                                showInfo(obj['speech']);
                                window.location.replace(urlAlbums);
                            }
                            break;

                        case "menu-radios":
                            if (window.location.pathname == urlIndex ) {
                                showInfo(obj['speech']);
                                window.location.replace(urlRadios);
                            }
                            break;
                    }


                }
                else {
                    if (!$('#lightbox-modal').is(":visible") && window.location.pathname == urlImages || window.location.pathname == urlVideos) {
                        showInfo(obj[0]['speech']);
                        addFilterImages(obj);                               //Añadimos las imagenes filtradas al documento

                        // focusImage($('img.img-responsive:first'));           // Hacemos foco en la primera imagen de todas.
                        $('img.img-responsive:first').addClass('focus');
                        $('video:first').addClass('focus');
                        // focusImage($('video:first'));
                    }
                    else
                    {
                        showError("Pruebe a escoger una opción del menú princial: Imágenes, Vídeos, Albums o Radios");
                    }

                }
            }
        }

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
    var current = 0;
    var imagelist = $('a[data-lightbox]').each(function (index) {
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


};

function anteriorImagen(){
    var current = 0;
    var imagelist = $('img.img-responsive').each(function (index) {
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
    var video = $('video.focus').prev();
    if ($('video.focus').hasClass('focus')){
        lightBox(video);
    }
    else{
        var image = $('img.focus').parent();
        lightBox(image, 'click');
    }

}

function showInfo(info) {
    var popUp = document.getElementById("infoBalloon");
    popUp.className = "balloon";
    while (popUp.firstChild) {
        popUp.removeChild(popUp.firstChild);
    }
    var alertIcon = document.createElement("i");
    alertIcon.className = "fas fa-check-circle";
    var elInfo = document.createElement("p");
    elInfo.innerHTML = info;
    alertIcon.appendChild(elInfo);
    popUp.appendChild(alertIcon);
    // popUp.appendChild(elInfo);
    popUp.style.visibility = "visible";
    popUp.style.display = "block";
    $(popUp).stop().fadeOut(3000);
}

function showError(error) {
    var popUp = document.getElementById("infoBalloon");
    popUp.className = "balloonError";
    while (popUp.firstChild) {
        popUp.removeChild(popUp.firstChild);
    }
    var alertIcon = document.createElement("i");
    alertIcon.className = 'fas fa-exclamation-triangle';
    alertIcon.style.fontSize = '3em';
    var elerror = document.createElement("p");
    elerror.innerHTML = error;

    // var elText = document.createElement("p");
    // elText.innerHTML = 'Prueba a decir: </br> <strong> Ver todas las fotos </strong>';
    popUp.appendChild(alertIcon);
    popUp.appendChild(elerror);
    // popUp.appendChild(elText);
    popUp.style.visibility = "visible";
    popUp.style.display = "block";
    $(popUp).stop().fadeOut(6000);
}

function addFilterImages(objects) {

    var elImgGrid = document.getElementById("imageGridAll");

    console.log("Resultado: " + objects + ". Nº de elementos: " + objects.length);

    //Si hay objetos en la consulta, eliminamos las imagenes del grid principal para mostrar las de la nueva consulta.
    while (elImgGrid.firstChild) {
        elImgGrid.removeChild(elImgGrid.firstChild);
    }

    // Recorremos el JSON para mostrar las fotos en el grid
    for (var i = 0; i < objects.length; i++) {
        var elDiv = document.createElement("div");
        var elTitle = document.createElement("h3");
        elTitle.className = "mg-md tc-mint-cream";
        var titulo = objects[i].titulo.substring(0,11);
        if ((objects[i].titulo).length > 11){
            titulo = titulo + '...'
        }
        elTitle.textContent = titulo;
        var elKey = document.createElement("p");
        var elA = document.createElement("a");
        elA.href = "#";
        elA.dataset.caption = objects[i].titulo;
        elA.dataset.lightbox = objects[i].src;
        elA.dataset.galleryId = "gallery-1";
        elA.dataset.frame = "fullscreen-lb";
        elKey.textContent = objects[i].keywords;
        if (objects[i]['type'] == "imagen"){
            $('h2.tc-honeydew').text("Galería de fotos");
            elDiv.className = "col-sm-2";
            var elImg = document.createElement("img");
            elImg.src = objects[i].src;
            elImg.dataset.src = objects[i].thumbnail;
            elImg.className ="img-responsive lazyload pulse-hvr animated";
            elA.appendChild(elImg);
        }
        else if (objects[i]['type'] == "video")
        {
            $('h2.tc-honeydew').text("Videoteca");
            elDiv.className = "col-sm-3";
            var videoContainer = document.createElement("div");
            videoContainer.className = "embed-responsive embed-responsive-16by9 animated swing-hvr";
            var elVid = document.createElement("video");
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
    };


}






function uploadAudioForm() {
    console.log("uploadAudioForm Function reached");
    recorder && recorder.exportWAV(function (blob) {
        saveAudioForm(blob);
        let form = document.getElementById("uploadAudioForm");
        console.log(form);
        form.submit();
    });
}
function saveAudioForm(blob) {
    var url = URL.createObjectURL(blob);
    let reader = new window.FileReader();
    reader.readAsDataURL(blob);
    reader.addEventListener("loadend", function () {
        var audioBase64 = reader.result.toString();
        let audioTurned = audioBase64.substr(audioBase64.indexOf(',')+1);
        document.getElementById("uploadAudioForm").elements.namedItem("audioBlob").value = audioTurned;
    })
}


/*function createDownloadLink() {
    recorder && recorder.exportWAV(function(blob) {
        var url = URL.createObjectURL(blob);
        var li = document.createElement('li');
        var au = document.createElement('audio');
        var hf = document.createElement('a');

        au.controls = true;
        au.src = url;
        hf.href = url;
        hf.download = new Date().toISOString() + '.wav';
        hf.innerHTML = hf.download;
        li.appendChild(au);
        li.appendChild(hf);
        recordingslist.appendChild(li);
    });
}*/

function clearLog() {
    document.getElementByID("log").innerHTML = "";
}

window.onload = function init() {
    try {
        //Webkit shim
        window.AudioContext = window.AudioContext || window.webkitAudioContext;
        navigator.getUserMedia = ( navigator.getUserMedia ||
                       navigator.webkitGetUserMedia ||
                       navigator.mozGetUserMedia ||
                       navigator.msGetUserMedia);

        audio_context = new AudioContext;
        // __log("Audio Context set up");
        // __log("navigator.getUserMedia " + (navigator.getUserMedia ? 'disponible.' : 'no disponible!'));
    } catch (e) {
        alert("Tu navegador no soporta grabación de voz. Consulta los requisitos de PiVoz")
        // __log("No web audio support in this browser!");
    }

    //Pedimos permisos de acceso a media:audio
    navigator.mediaDevices.getUserMedia({audio: true}).then(startUserMedia);
    // navigator.mediaDevices.getUserMedia({audio: true}, startUserMedia, function (e) {
    //
    // });


}


