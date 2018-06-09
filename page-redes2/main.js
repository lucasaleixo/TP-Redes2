$(document).ready(function() {
    $(function(){
        $('.targetDiv').hide();
        $('.active').click(function(){
            $('.targetDiv').hide();
            $("#titulo").show();
        });
        
        $('.showSingle').click(function(){
              $("#titulo").hide();
              $('.targetDiv').hide();
              $('#div'+$(this).attr('target')).show();
        });

        $('.showSingle').click(function(){
              $('.targetDiv').hide();
              $('#div'+$(this).attr('target')).show();
        });
    });
});
