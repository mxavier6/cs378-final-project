[![MIT licensed](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/hyperium/hyper/master/LICENSE)

#Helm-YouTube
<p align="center">
  <img src="https://github.com/maximus12793/helm-youtube/blob/master/demo.gif">
</p>

Helm-YouTube is a simple plugin to query YouTube via emacs and play videos in your browser. 

**IMPORTANT:** Remeber to set your 'helm-youtube-key' variable!

## Installation 
1. M-x package-install: helm-youtube

2. Obtain new google API key 
    [here](https://console.developers.google.com/ "Google Developer Console")

    ![Screenshot](https://github.com/maximus12793/helm-youtube/blob/master/api.png)

3. **IMPORTANT:** Set 'helm-youtube-key' variable


    ``` el
    M-x customize-variable ;; search 'helm-youtube-key'
    Helm Youtube Key: replace "NONE" with "API KEY" ;; FROM STEP 2
    ```

4. Set browse-url-generic and add to .emacs

 
