# ScrapeImagesPY

On run, supply with initial website URL and depth (number) of how much links it should enter.<br>
For example: python crawler.py https://barakadax.github.io/ 2:<br>
<img src="treeExample.png" title="Example" alt="Sample of hierarchy"><br>
Creates folder with each website name and download the picture inside each website folder.<br>
In the end create JSON file with: website url, picture url and in which depth the picture was found.<br>
In this exercise I used to go into other links the &lt;url&gt; that I never seen in other websites, for it to work properly need to change to &lt;a&gt; tag.
