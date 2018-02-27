
// slug related js
// reference:
//   https://gist.github.com/mathewbyrne/1280286
//   https://stackoverflow.com/questions/8340719/

function slugify(text)
{
  return text.toString().toLowerCase()
    .replace(/\s+/g, '-')           // Replace spaces with -
//    .replace(/[^\w\-]+/g, '')       // Remove all non-word chars
	.replace(/['`~!@#$%^&*()_|+=—…，（）‘’“”：、·！？?;:'",.<>\{\}\[\]\\\/]/gi, '')
	// Remove all non-word chars, keep unicode 
    .replace(/\-\-+/g, '-')         // Replace multiple - with single -
    .replace(/^-+/, '')             // Trim - from start of text
    .replace(/-+$/, '');            // Trim - from end of text
}
$(document).ready(function(){
        $('input[name=name]').on('input propertychange', function() {
         var nametext = $(this).val();
         $('input[name=slug]').val(slugify(nametext));
        });
      });
