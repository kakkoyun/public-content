<!-- slide bg="#632CA6" -->

<grid drag="100 6" drop="top" align="left" pad="0 20px" style="font-size: 16px;">
 <%? title %>
</grid>

<% content %>

<style>
.reveal .slides section[data-background-color="#632ca6"] h1,
.reveal .slides section[style*="background-color: rgb(99, 44, 166)"] h1,
.reveal .slides section[style*="background-color: #632ca6"] h1,
.reveal .slides section[style*="background-color: #632CA6"] h1 {
  color: white !important;
}
.horizontal_dotted_line{
  border-bottom: 2px dotted white !important;
}
</style>

<grid drag="94 0" drop="3 -6" class="horizontal_dotted_line">
</grid>

<grid drag="100 30" drop="0 64" align="bottomleft" pad="0 30px" style="font-size: 13px;" class="small-indent">
<%? source %>
</grid>

<grid drag="100 2" drop="bottom">
![[dd_logo_h_white.png]]
</grid>
