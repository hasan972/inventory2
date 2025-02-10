// sidebar start
var activeLinks = document.querySelectorAll('.active_link');
activeLinks.forEach(function(link) {
    var subMenuList = $(link).parent().closest('.sub-menu-list');
    subMenuList.css('display', 'block');
    var menuItem = $(link).parent().closest('.sub-menu');
    if (menuItem) {
        $(menuItem).addClass('open');    
    }
});
// sidebar close

// common start
$(document).ready(function() {
    // custom input controll
    $("#btn_view, #btn_edit").on( "click", function() {
        $("#btn_view").toggleClass("d-none");
        $("#btn_edit").toggleClass("d-none");
        $("#edit_view_section").toggleClass("d-none");
        
        $("input").toggleClass("is_enable");
        $(".select2-container").toggleClass("is_enable");
        $('input[type="checkbox"]').each(function() {
            var $this = $(this);
            $this.prop('disabled', !$this.prop('disabled'));
        });
    });
    // custom input controll
  
    // For Delete button   swiftalert
    $(document).on("click", "#delete_btn", function(e) {
        e.preventDefault();
        //const href = $(this).attr('href');
        
        Swal.fire({
            title: "Are you sure?",
            text: "You won't be able to revert this!",
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#3085d6",
            cancelButtonColor: "#d33",
            confirmButtonText: "Yes, delete it!"
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = $(this).attr('href');;
            }
        });
    });
    // For Delete button   swiftalert

});
// common end


// Function to convert table cell to input datatable
function convertToInput(element) {
    var text = element.innerText;
    var input = document.createElement("input");
    input.type = "text";
    input.value = text;
    input.className = "custom-input";
    var actionHandled = false;

    function updateCellValue() {
        if (!actionHandled) {
            actionHandled = true;
            element.innerText = input.value;
            console.log("Value changed to: " + input.value);
            actionHandled = false;
        }
    }

    input.addEventListener("blur", updateCellValue);
    input.addEventListener("keyup", function(event) {
        if (!actionHandled && event.key === "Enter") {
            updateCellValue();
        }
    });
    
    element.innerText = '';
    element.appendChild(input);
    input.focus();
}

// Attach click event listener to table cells
function cellEditable(element) {
  var cells = document.querySelectorAll("td.custom-td");
  cells.forEach(function(cell) {
      cell.addEventListener("click", function() {
          convertToInput(this);
      });
  });
}

// datatable close