document.addEventListener("DOMContentLoaded", () => {

    // =========================
    // SCRIPT UPLOAD
    // =========================

    const scriptFile = document.getElementById("scriptFile");
    const chooseScriptBtn = document.getElementById("chooseScriptBtn");
    const uploadScriptBtn = document.getElementById("uploadScriptBtn");

    const selectedScript = document.getElementById("selectedScript");
    const scriptStatus = document.getElementById("scriptStatus");

    const scriptProgress = document.getElementById("scriptProgress");
    const scriptProgressBar = document.getElementById("scriptProgressBar");
    const scriptProgressText = document.getElementById("scriptProgressText");

    const improveScriptBtn =
        document.getElementById("improveScriptBtn");

    const aiStatus =
        document.getElementById("aiStatus");

    const originalScriptBox =
        document.getElementById("originalScriptBox");

    const originalScriptText =
        document.getElementById("originalScriptText");

    const improvedScriptBox =
        document.getElementById("improvedScriptBox");

    const improvedScriptText =
        document.getElementById("improvedScriptText");

    const downloadScriptBtn =
        document.getElementById("downloadScriptBtn");


    let selectedScriptFile = null;
    let uploadedScriptId = null;


    // Choose script

    chooseScriptBtn.addEventListener("click", () => {
        scriptFile.click();
    });


    // Script selected

    scriptFile.addEventListener("change", () => {

        selectedScriptFile = scriptFile.files[0];

        if (!selectedScriptFile) {
            return;
        }

        selectedScript.textContent =
            "📄 " + selectedScriptFile.name;

        scriptStatus.textContent =
            "Script selected. Ready to upload.";

        uploadScriptBtn.disabled = false;
    });


    // Upload script

    uploadScriptBtn.addEventListener("click", () => {

        if (!selectedScriptFile) {

            scriptStatus.textContent =
                "❌ Please choose a script first.";

            return;
        }


        const formData = new FormData();

        formData.append(
            "script",
            selectedScriptFile
        );


        uploadScriptBtn.disabled = true;

        uploadScriptBtn.textContent =
            "⏳ Uploading...";


        scriptProgress.style.display =
            "block";

        scriptProgressBar.value = 0;

        scriptProgressText.textContent =
            "Uploading: 0%";


        const xhr = new XMLHttpRequest();

        xhr.open(
            "POST",
            "/api/upload-script",
            true
        );


        xhr.upload.onprogress = (event) => {

            if (!event.lengthComputable) {
                return;
            }

            const percent =
                Math.round(
                    (event.loaded / event.total) * 100
                );

            scriptProgressBar.value =
                percent;

            scriptProgressText.textContent =
                `Uploading: ${percent}%`;
        };


        xhr.onload = () => {

            try {

                const data =
                    JSON.parse(xhr.responseText);


                if (
                    xhr.status >= 200 &&
                    xhr.status < 300 &&
                    data.success
                ) {

                    uploadedScriptId =
                        data.script_id;


                    scriptProgressBar.value =
                        100;

                    scriptProgressText.textContent =
                        "Upload complete: 100%";


                    scriptStatus.textContent =
                        "✅ Original script uploaded";


                    uploadScriptBtn.textContent =
                        "✅ Script Uploaded";


                    improveScriptBtn.disabled =
                        false;


                    // Read original script locally
                    const reader =
                        new FileReader();


                    reader.onload = (event) => {

                        originalScriptText.value =
                            event.target.result;

                        originalScriptBox.style.display =
                            "block";
                    };


                    reader.readAsText(
                        selectedScriptFile
                    );


                } else {

                    throw new Error(
                        data.error ||
                        "Script upload failed"
                    );
                }


            } catch (error) {

                scriptStatus.textContent =
                    "❌ " + error.message;

                uploadScriptBtn.disabled =
                    false;

                uploadScriptBtn.textContent =
                    "⬆️ Upload Script";
            }
        };


        xhr.onerror = () => {

            scriptStatus.textContent =
                "❌ Network error";

            uploadScriptBtn.disabled =
                false;

            uploadScriptBtn.textContent =
                "⬆️ Upload Script";
        };


        xhr.send(formData);
    });


    // =========================
    // 9ROUTER AI
    // =========================

    improveScriptBtn.addEventListener(
        "click",
        async () => {

            if (!uploadedScriptId) {

                aiStatus.textContent =
                    "❌ Please upload the original script first.";

                return;
            }


            const language =
                document.getElementById(
                    "languageSelect"
                ).value;


            const style =
                document.getElementById(
                    "styleSelect"
                ).value;


            improveScriptBtn.disabled =
                true;

            improveScriptBtn.textContent =
                "⏳ 9Router AI is improving script...";


            aiStatus.textContent =
                "🤖 Sending original script to 9Router AI...";


            try {

                const response =
                    await fetch(
                        "/api/improve-script",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({

                                script_id:
                                    uploadedScriptId,

                                language:
                                    language,

                                style:
                                    style
                            })
                        }
                    );


                const data =
                    await response.json();


                if (
                    !response.ok ||
                    !data.success
                ) {

                    throw new Error(
                        data.error ||
                        "AI script generation failed"
                    );
                }


                improvedScriptText.value =
                    data.text;


                improvedScriptBox.style.display =
                    "block";


                aiStatus.textContent =
                    "✅ 9Router AI successfully improved your script.";


                improveScriptBtn.textContent =
                    "✅ SCRIPT IMPROVED";


            } catch (error) {

                aiStatus.textContent =
                    "❌ " + error.message;


                improveScriptBtn.disabled =
                    false;


                improveScriptBtn.textContent =
                    "✨ IMPROVE SCRIPT WITH 9ROUTER";
            }
        }
    );


    // =========================
    // DOWNLOAD IMPROVED SCRIPT
    // =========================

    downloadScriptBtn.addEventListener(
        "click",
        () => {

            const text =
                improvedScriptText.value;


            if (!text.trim()) {
                return;
            }


            const blob =
                new Blob(
                    [text],
                    {
                        type:
                            "text/plain;charset=utf-8"
                    }
                );


            const url =
                URL.createObjectURL(blob);


            const a =
                document.createElement("a");


            a.href = url;

            a.download =
                "improved_movie_script.txt";


            document.body.appendChild(a);

            a.click();

            a.remove();

            URL.revokeObjectURL(url);
        }
    );


    // =========================
    // VIDEO UPLOAD
    // =========================

    const videoFile =
        document.getElementById("videoFile");

    const chooseVideoBtn =
        document.getElementById("chooseVideoBtn");

    const uploadBtn =
        document.getElementById("uploadBtn");

    const selectedFile =
        document.getElementById("selectedFile");

    const status =
        document.getElementById("uploadStatus");

    const progressBox =
        document.getElementById("uploadProgress");

    const progressBar =
        document.getElementById("progressBar");

    const progressText =
        document.getElementById("progressText");


    let selectedVideo = null;


    chooseVideoBtn.addEventListener(
        "click",
        () => {
            videoFile.click();
        }
    );


    videoFile.addEventListener(
        "change",
        () => {

            selectedVideo =
                videoFile.files[0];

            if (!selectedVideo) {
                return;
            }


            selectedFile.textContent =
                "🎬 " + selectedVideo.name;


            status.textContent =
                "Video selected. Ready to upload.";


            uploadBtn.disabled =
                false;
        }
    );


    uploadBtn.addEventListener(
        "click",
        () => {

            if (!selectedVideo) {

                status.textContent =
                    "❌ Please choose a video first.";

                return;
            }


            const formData =
                new FormData();


            formData.append(
                "video",
                selectedVideo
            );


            uploadBtn.disabled =
                true;

            uploadBtn.textContent =
                "⏳ Uploading...";


            progressBox.style.display =
                "block";


            progressBar.value =
                0;


            progressText.textContent =
                "Uploading: 0%";


            const xhr =
                new XMLHttpRequest();


            xhr.open(
                "POST",
                "/api/upload-video",
                true
            );


            xhr.upload.onprogress =
                (event) => {

                    if (
                        !event.lengthComputable
                    ) {
                        return;
                    }


                    const percent =
                        Math.round(
                            (event.loaded /
                             event.total) * 100
                        );


                    progressBar.value =
                        percent;


                    progressText.textContent =
                        `Uploading: ${percent}%`;
                };


            xhr.onload = () => {

                try {

                    const data =
                        JSON.parse(
                            xhr.responseText
                        );


                    if (
                        xhr.status >= 200 &&
                        xhr.status < 300 &&
                        data.success
                    ) {

                        progressBar.value =
                            100;


                        progressText.textContent =
                            "Upload complete: 100%";


                        status.textContent =
                            "✅ Video uploaded successfully";


                        uploadBtn.textContent =
                            "✅ Video Uploaded";


                        console.log(
                            "Video Job ID:",
                            data.job_id
                        );


                    } else {

                        throw new Error(
                            data.error ||
                            "Upload failed"
                        );
                    }


                } catch (error) {

                    status.textContent =
                        "❌ " + error.message;


                    uploadBtn.disabled =
                        false;


                    uploadBtn.textContent =
                        "⬆️ Upload Video";
                }
            };


            xhr.onerror = () => {

                status.textContent =
                    "❌ Network error";


                uploadBtn.disabled =
                    false;


                uploadBtn.textContent =
                    "⬆️ Upload Video";
            };


            xhr.send(formData);
        }
    );

});
