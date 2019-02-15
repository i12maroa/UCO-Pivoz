//JavaScript

recorder.addEventListener("dataAvailable", function (e) {
                var fileName = new Date().toISOString() + "." + e.detail.type.split("/")[1];
                var url = URL.createObjectURL(e.detail);
                var audio = document.createElement('audio');
                audio.controls = true;
                audio.src = url;

                var link = document.createElement('a');
                link.href = url;
                link.download = fileName;
                link.innerHTML = link.download;

                //New Code starts here
                var progress = document.createElement('progress');
                progress.min = 0;
                progress.max = 100;
                progress.value = 0;
                var progressText = document.createTextNode("Progress: ");

                var button = document.createElement('button');
                var t = document.createTextNode('Upload?');
                button id = 'button';
                button.appendChild(t);
                button.onclick = function(){
                    upload(e.detail, progress);
                };

                // All that's left is to add the button and Progress bar to the list
                var li = document.createElement('li');
                li.appendChild(link);
                li.appendChild(audio);
                li.appendChild(button);
                li.appendChild(progressText);
                li.appendChild(progress);

                recordingslist.appendChild(li)

            });