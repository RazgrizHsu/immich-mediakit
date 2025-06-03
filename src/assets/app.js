document.addEventListener( 'keydown', function ( ev ){
	const modal = document.querySelector( '#img-modal' )

	if ( modal && modal.parentElement.classList.contains('show') )
	{
		if ( ev.key == 'ArrowLeft' || ev.key == 'h' )
		{
			ev.preventDefault();
			const btn = document.querySelector( '#btn-img-prev' );
			if ( btn && btn.style.opacity != '0.3' ) btn.click();
		}
		else if ( ev.key == 'ArrowRight' || ev.key == 'l' )
		{
			ev.preventDefault();
			const btn = document.querySelector( '#btn-img-next' );
			if ( btn && btn.style.opacity != '0.3' ) btn.click();
		}
		else if ( ev.key == ' ' )
		{
			ev.preventDefault();
			const btn = document.querySelector( '#btn-img-select' );
			if ( btn && btn.style.display !== 'none' ) btn.click();
		}
		else if ( ev.key == 'Escape' || ev.key == 'q' )
		{
			ev.preventDefault();
			const btn = modal.querySelector( '.btn-close' );
			if ( btn ) btn.click();
		}
		else if ( ev.key == 'm' )
		{
			ev.preventDefault();
			const btn = modal.querySelector( '#btn-img-mode' );
			if ( btn ) btn.click();
		}
		else if ( ev.key == '?' )
		{
			ev.preventDefault();
			const btn = modal.querySelector( '#btn-img-help' );
			if ( btn ) btn.click();
		}
	}
} );
