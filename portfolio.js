let button= document.getElementById("menu-button");
let cancel=document.getElementById("cancel-button");
let box=document.getElementById("drop-down");
let links=document.querySelectorAll("links");
let nav=document.getElementById("nav-bar");
let container1=document.getElementById("container1")
let page=document.getElementById("contacts-content")
button.addEventListener("click",function(){
    box.style.width="100%";
    box.style.transition="linear 1s";
})
cancel.addEventListener("click",function(){
      box.style.width="0%"
      nav.style.display="block"
})

for (let index = 0; index < document.querySelectorAll(".contact-screen").length; index++) {
   document.querySelectorAll(".contact-screen")[index].addEventListener("click", function(){
    container1.style.display="none";
    page.style.display="block";
    document.getElementById("hire-content").style.display="none"
    document.getElementById("aboutme-content").style.display="none";
    document.getElementById("drop-down").style.width="0%";
    document.getElementById("screen-state").innerHTML="CONTACT";
     document.getElementById("screen-state").style.width="70px";
})
}
for (let index = 0; index < document.querySelectorAll(".about-me").length; index++) {
  document.querySelectorAll(".about-me")[index].addEventListener("click", function(){
    document.getElementById("aboutme-content").style.display="block";
        container1.style.display="none";
        page.style.display="none";
        document.getElementById("hire-content").style.display="none"
        document.getElementById("drop-down").style.width="0%";
        document.getElementById("screen-state").innerHTML="ABOUT ME";
        document.getElementById("screen-state").style.width="80px"
        document.getElementById("screen-state").style.fontSize="0.9em"
}) 
}
 for (let index = 0; index <document.querySelectorAll(".Hire-page").length; index++) {
  document.querySelectorAll(".Hire-page")[index].addEventListener("click", function(){
    document.getElementById("screen-state").innerHTML="HIRE ME";
    page.style.display="none"
   document.getElementById("drop-down").style.width="0%";
    document.getElementById("hire-content").style.display="block"
    document.getElementById("screen-state").style.width="65px"
    document.getElementById("screen-state").style.fontSize="0.9em"
   container1.style.display="none";
   document.getElementById("aboutme-content").style.display="none"
})
 }