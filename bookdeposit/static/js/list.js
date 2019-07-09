$(document).ready(function() {
	$.get("/api/v1/list", function(data) {
		// console.log(data);

		$.each(data, function() {

			if (this.status == "SUCCESS") {
				this.badge = "success"
				this.badge_label = "VALID"
			} else if (this.status == "FAILURE") {
				this.badge = "danger"
				this.badge_label = "INVALID"
			}

			this.fmtDate = this.date.substr(0,10)
			this.fmtTime = this.date.substr(11,5)


			// console.log(this.bag_uuid);
			var template = $('#template').html();
			Mustache.parse(template);
			var rendered = Mustache.render(template, this);
			$('#deposit_list').append(rendered);
		})

	});

});