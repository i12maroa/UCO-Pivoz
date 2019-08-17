/** Script para el funcionamiento de PiVoz
* @license Antonio Maestre Rosa
* @Copyright (c) 2018 Copyright Holder All Rights Reserved.
*/


var audio_context;
var recorder;


/**
*  Situa la página en el elemento seleccionado
*/
$.fn.scrollView = function () {
  return this.each(function () {
    $('html, body').animate({
      scrollTop: $(this)
    }, 1000);
  });
}

/**
*  Devuelve el valor de la cookie con la clave name
*  @param {string} name Nombre de la cookie
*  @return {string} cookieValue Valor de la cookie name
*/
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
    } return cookieValue;
}

/**
*  Alimenta al grabador de audio con el stream de audio
*  @param {object} stream Chunk de audio
*
*/
function startUserMedia(stream){
    var input = audio_context.createMediaStreamSource(stream);
    audio_context.resume();
    __log('Media stream created.');

    //Inicializamos el recorder y le pasamos el stream de audio que creamos previamente para que lo use para grabar
    recorder = new Recorder(input);
    __log('Recorder initialised');

    // Comenzamos a detectar comandos de voz
    detecteSilence(stream, onSilence, onSpeak, 1000, -80, audio_context);
}


/**
*  Muestra mensajes de log en la consola JavaScript
*  @param {Event}  e Evento capturado
*  @param {String} data Mensage de log
*/
function __log(e, data){
    console.log("\n" + e + " " + (data || ''));
}

/**
*  Inicia la grabación de voz
*  @param {HTMLBodyElement}  button botón de micrófono
*/
function startRecording(button) {
    audio_context.resume();
    recorder && recorder.record();
    __log("Start Recording");
};

/**
*  Detiene la grabación de voz
*  @param {HTMLBodyElement}  button botón de micrófono
*/
function stopRecording(button) {
    recorder && recorder.stop();

    __log("Stopped Recording");

    //Enviamos el audio
    makeLink();

    recorder.clear();
    audio_context.resume().then(() => {
    __log('Playback resumed successfully');
    });


}

/**
 * Detecta cuando el ruido ambiente por encima de un umbral determinado
 * @param  {stream} stream Stream de audio
 * @param  {function} onSoundEnd función a ejecutar cuando el usuario termina de hablar
 * @param  {function} onSoundStart función a ejecutar cuando el usuario empieza a hablar
 * @param  {number} silence_delay tiempo en milisegundos que transcurre desde que se detecta el silencio hasta que
 *                                          se ejecuta la función onSoundEnd
 * @param   {number} min_decibels  nivel de ruido a partir se ejecuta la función onSoundStart
 * @param   {audioContext} AudioContext objeto AudioContext
 */
function detecteSilence(stream, onSoundEnd = _=>{}, onSoundStart = _=>{}, silence_delay = 500, min_decibels = 50, audioContext) {
    const ctx = audioContext;
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

/**
 * Función para subir el audio al servidor y ejecutar una respuesta
 * @license Antonio Maestre Rosa
 */


function makeLink() {
    recorder && recorder.exportWAV(function (blob) {
        let fd = new FormData();
        let obj = "";
        fd.append("audio", blob, "speech");
        // Creamos el token de seguridadd CSRF_TOKEN
        let csrftoken = getCookie('csrftoken');
        // Llamada AJAX
        let xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
            if (this.readyState === 4 && this.status === 200) {
                obj = JSON.parse(this.responseText);
                __log("JSON response:" + JSON.stringify(obj) + ". JSON lenght: " + obj.length);
                if (obj['error']){
                    showError(obj['error']);
                }
                else if (obj['comando']){
                    switch (obj['comando']) {
                        case "ver":
                            if (window.location.pathname === urlIndex){showError("Pruebe a escoger una opción del menú princial: Imágenes, Vídeos, Albums o Radios");break;}
                            __log("El usuario quiere ver las imagenes");
                            if($(".focus")[0]){
                                if (!$('#lightbox-modal').is(":visible")){
                                    verImagen();
                                    showInfo(obj[0]['speech']);
                                }
                            }

                            break;

                        case "siguiente":
                            if (window.location.pathname === urlIndex){showError("Pruebe a escoger una opción del menú princial: Imágenes, Vídeos, Albums o Radios");break;}
                            console.log("Siguiente Imagen");
                            siguienteImagen();
                            showInfo("Comando: Siguiente");
                            break;

                        case "anterior":
                            if (window.location.pathname === urlIndex){showError("Pruebe a escoger una opción del menú princial: Imágenes, Vídeos, Albums o Radios");break;}
                            __log("Imagen anterior");
                            showInfo("Comando: Anterior");
                            anteriorImagen();
                            break;

                        case "salir":
                            var modal = $('#lightbox-modal');
                            if (modal.is(":visible")){
                                showInfo("Comando: Salir");
                                modal.remove();
                                $('div.modal-backdrop').remove();
                                $('body').removeClass('modal-open');
                            }
                            break;

                        case "volumeUp":

                            if (video.length !== 0 && !video.paused){
                                let volume = video.prop('volume');
                                let newVolume = volume + 0.1;
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
                                let newVolume = volume - 0.1;
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
                            if (window.location.pathname === urlIndex ){
                                showInfo(obj['speech']);
                                window.location.replace(urlImages);
                            }
                            break;

                        case "menu-videos":
                            if (window.location.pathname === urlIndex ){
                                showInfo(obj['speech']);
                                window.location.replace(urlVideos);
                            }
                            break;

                        case "menu-albums":
                            if (window.location.pathname === urlIndex ) {
                                showInfo(obj['speech']);
                                window.location.replace(urlAlbums);
                            }
                            break;

                        case "menu-radios":
                            if (window.location.pathname === urlIndex ) {
                                showInfo(obj['speech']);
                                window.location.replace(urlRadios);
                            }
                            break;
                            case "profile":
                                if (window.location.pathname === urlIndex) {
                                    showInfo(obj['speech']);
                                    window.location.replace(urlProfile);
                                }
                                break;
                    }


                }
                else {
                    if (obj['type'] === "radio"){
                        if (window.location.pathname === urlRadios ) {
                            let index = 0;
                            showInfo(obj['speech']);
                            __log("Nombre emisora:"+ obj['titulo']);
                            switch (obj['titulo']) {
                                case "Cadena 100":
                                    index = 0;
                                    break;
                                case "Cadena Cope":
                                    index = 1;
                                    break;
                                case "Cadena Dial":
                                    index = 2;
                                    break;
                                case "Europa FM":
                                    index = 3;
                                    break;
                                case "Máxima FM":
                                    index = 4;
                                    break;
                                case "Los cuarenta principales":
                                    index = 5;
                                    break;
                                case "Canal Sur Radio":
                                    index = 6;
                                    break;
                                case "Rock FM":
                                    index = 7;
                                    break;
                            }
                            radio.stop();
                            radio.play(index);
                        }
                        else{
                            showError("Debes estar en el menú de radios para poner una emisora. Prueba antes a decir 'pivoz radios'");
                        }
                    }

                    if (!$('#lightbox-modal').is(":visible") && window.location.pathname === urlImages || window.location.pathname === urlVideos) {
                        showInfo(obj[0]['speech']);
                        addFilterImages(obj);                               //Añadimos las imagenes filtradas al documento

                        $('img.img-responsive:first').addClass('focus');
                        $('video:first').addClass('focus');
                    }
                    else
                    {
                        showError("Pruebe a escoger una opción del menú princial: Imágenes, Vídeos, Albums o Radios");
                    }

                }
            }
        }

        xhr.open('POST', uploadAudio_url , true);
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
        xhr.onerror = function (e) {
            alert("Error en el servidor al subir el audio. Contacte con el administrador.");
            __log("Error Uploading audio" + e)
        };

        xhr.send(fd);
    });

}

/* Pasar a la siguiente imagen */
function siguienteImagen() {
    var current = 0;
    var imagelist = $('a[data-lightbox]').each(function (index) {
        if ($(this).children(":first-child").hasClass('focus')){
            current = index;
        }
    });
    if (imagelist.length !== 1) {                                        // En caso de que solo haya una imagen, no nos movemos.
        $(imagelist).eq(current).children(":first-child").removeClass('focus pulse');
        if (current == imagelist.length - 1) { current = -1 };          // En caso de ser la ultima imagen. La siguiente sera la primera
        $(imagelist).eq(current+1).children(":first-child").addClass('focus pulse');
        $('.focus').scrollView();
        var container = $('html,body'),
             scrollTo = $('.focus');

        container.animate({
            scrollTop: scrollTo.offset().top - container.offset().top
        });


        slide($(imagelist).eq(current), "next");
    }else {
        showError("Sólo hay una foto. No puedes utilizar el comando siguiente")
    }

}

/* Navegar a la imagen anterior */
function anteriorImagen(){
    var current = 0;
    var imagelist = $('img.img-responsive').each(function (index) {
        if ($(this).hasClass('focus')) {
            current = index;
        }
    });
    if (imagelist.length !== 1) {                                              // En caso de que solo haya una imagen, no nos movemos.
        $(imagelist).eq(current).removeClass('focus pulse');
        if (current === 0) {
            current = imagelist.length;
        };
        $(imagelist).eq(current - 1).addClass('focus pulse');
        slide($(imagelist).eq(current).parent(), "previous");
    }else {
        showError("Sólo hay una foto. No puedes utilizar el comando anterior")
    }
}

/** Función que abre una ventana modal con la imagen o video seleccionad@ ampliad@
*   En el caso de ser un álbum, mostrará el contenido del álbum.
*/
function verImagen() {
    var video = $('video.focus');
    var album = $('img.focus').parent();

    if (video.length){
        lightBox(video);
    }
    else if(album.attr('data-type')==="album"){
        console.log("Entra album");
        window.location.replace(album.attr('href'));
    }
    else{
        var image = $('img.focus').parent();
        lightBox(image, 'click');
    }

}

/**
*  Muestra un mensaje de éxito en la interfaz de usuario
*  @param {string} info Mensaje que se mostrará
*
*/
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
    popUp.style.visibility = "visible";
    popUp.style.display = "block";
    $(popUp).stop().fadeOut(4000);
}

/**
*  Muestra un mensaje de error en la interfaz de usuario
*  @param {string} error Mensaje que se mostrará
*
*/
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
    popUp.appendChild(alertIcon);
    popUp.appendChild(elerror);
    popUp.style.visibility = "visible";
    popUp.style.display = "block";
    $(popUp).stop().fadeOut(6000);
}

/**
*  Rellena un grid de imágenes, vídeos o álbumes
*  @param {object} objects Objeto que puede ser Imagen o Vídeo
*
*/
function addFilterImages(objects) {

    var elImgGrid = document.getElementById("imageGridAll");

    console.log("Resultado: " + objects + ". N de elementos: " + objects.length);

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
        elA.dataset.lightbox = objects[i].src;
        elA.dataset.galleryId = "gallery-1";
        elA.dataset.frame = "fullscreen-lb";
        elKey.textContent = objects[i].keywords;
        if (objects[i]['type'] === "imagen"){
            $('h2.tc-honeydew').text("Galería de fotos");
            elDiv.className = "col-sm-2";
            var elImg = document.createElement("img");
            elImg.src = objects[i].src;
            elImg.dataset.src = objects[i].thumbnail;
            elImg.className ="img-responsive lazyload pulse-hvr animated";
            elA.dataset.caption = objects[i].titulo;
            elA.appendChild(elImg);
        }
        else if (objects[i]['type'] === "video")
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
            elVid.dataset.frame = "fullscreen-lb";
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


// Cache references to DOM elements.
var elms = ['station0', 'title0', 'live0', 'playing0', 'station1', 'title1', 'live1', 'playing1', 'station2', 'title2', 'live2', 'playing2', 'station3', 'title3', 'live3', 'playing3', 'station4', 'title4', 'live4', 'playing4'];
elms.forEach(function(elm) {
  window[elm] = document.getElementById(elm);
});

/**
 * Radio class containing the state of our stations.
 * Includes all methods for playing, stopping, etc.
 * @param {Array} stations Array of objects with station details ({title, src, howl, ...}).
 */
var Radio = function(stations) {
  var self = this;

  self.stations = stations;
  self.index = 0;

  // Setup the display for each station.
  for (var i=0; i<self.stations.length; i++) {
    window['title' + i].innerHTML = '<b>' + self.stations[i].freq + '</b> ' + self.stations[i].title;
    window['station' + i].addEventListener('click', function(index) {
      var isNotPlaying = (self.stations[index].howl && !self.stations[index].howl.playing());

      // Stop other sounds or the current one.
      radio.stop();

      // If the station isn't already playing or it doesn't exist, play it.
      if (isNotPlaying || !self.stations[index].howl) {
        radio.play(index);
      }
    }.bind(self, i));
  }
};
Radio.prototype = {
  /**
   * Play a station with a specific index.
   * @param  {Number} index Index in the array of stations.
   */
  play: function(index) {
    var self = this;
    var sound;

    index = typeof index === 'number' ? index : self.index;
    var data = self.stations[index];

    // If we already loaded this track, use the current one.
    // Otherwise, setup and load a new Howl.
    if (data.howl) {
      sound = data.howl;
    } else {
      sound = data.howl = new Howl({
        src: data.src,
        html5: true, // A live stream can only be played through HTML5 Audio.
        format: ['mp3', 'aac']
      });
    }

    // Begin playing the sound.
    sound.play();

    // Toggle the display.
    self.toggleStationDisplay(index, true);

    // Keep track of the index we are currently playing.
    self.index = index;
  },

  /**
   * Stop a station's live stream.
   */
  stop: function() {
    var self = this;

    // Get the Howl we want to manipulate.
    var sound = self.stations[self.index].howl;

    // Toggle the display.
    self.toggleStationDisplay(self.index, false);

    // Stop the sound.
    if (sound) {
      sound.stop();
    }
  },

  /**
   * Toggle the display of a station to off/on.
   * @param  {Number} index Index of the station to toggle.
   * @param  {Boolean} state true is on and false is off.
   */
  toggleStationDisplay: function(index, state) {
    var self = this;

    // Highlight/un-highlight the row.
    window['station' + index].style.backgroundColor = state ? 'rgba(255, 255, 255, 0.33)' : '';

    // Show/hide the "live" marker.
    window['live' + index].style.opacity = state ? 1 : 0;

    // Show/hide the "playing" animation.
    window['playing' + index].style.display = state ? 'block' : 'none';
  }
};

/**
*  Inicialización del audio
*/
window.onload = function init() {
    try {
        //Webkit shim
        window.AudioContext = window.AudioContext || window.webkitAudioContext;
        navigator.getUserMedia = (navigator.getUserMedia ||
            navigator.webkitGetUserMedia ||
            navigator.mozGetUserMedia ||
            navigator.msGetUserMedia);

        audio_context = new AudioContext;
        __log("Audio Context set up");
        __log("navigator.getUserMedia " + (navigator.getUserMedia ? 'disponible.' : 'no disponible!'));
    } catch (e) {
        alert("Tu navegador no soporta grabación de voz. Consulta los requisitos de PiVoz");
    }

    //Pedimos permisos de acceso a media:audio
    navigator.mediaDevices.getUserMedia({audio: true}).then(startUserMedia);

};
