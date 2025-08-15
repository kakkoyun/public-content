<!-- slide bg="white" -->

<grid drag="100 6" drop="top" align="left" pad="0 20px" style="font-size: 16px">
 <%? title %>
</grid>

<% content %>

<style>
.reveal .slides section[data-background-color="white"] h1,
.reveal .slides section[style*="background-color: white"] h1,
.reveal .slides section[style*="background-color: rgb(255, 255, 255)"] h1,
.reveal .slides section:not([data-background-color]):not([style*="background"]) h1 {
  color: #632CA6 !important;
}
.horizontal_dotted_line_light{
  border-bottom: 2px dotted #632CA6 !important;
}
</style>

<grid drag="94 0" drop="3 -6" class="horizontal_dotted_line_light">
</grid>

<grid drag="100 30" drop="0 64" align="bottomleft" pad="0 30px" style="font-size: 13px;" class="small-indent">
<%? source %>
</grid>

<grid drag="100 2" drop="bottom">
![[dd_logo_h_rgb.png]]
</grid>
