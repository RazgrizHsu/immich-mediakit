document.addEventListener( 'keydown', function ( event ){
	const modal = document.querySelector( '#img-modal' )

	// console.info( `[keydown] event.key[ ${event.key} ]` )
	if ( modal && modal.parentElement.classList.contains('show') )
	{
		if ( event.key === 'ArrowLeft' )
		{
			event.preventDefault();
			const btn = document.querySelector( '#btn-img-prev' );
			if ( btn && btn.style.opacity != '0.3' )
			{
				console.info( `[img-pop] click prev` )
				btn.click();
			}
			else {
				console.info( `[img-pop] no: ${btn}` )
			}
		}
		else if ( event.key === 'ArrowRight' )
		{
			event.preventDefault();
			const btn = document.querySelector( '#btn-img-next' );
			if ( btn && btn.style.opacity != '0.3' )
			{
				console.info( `[img-pop] click next` )
				btn.click();
			}
			else {
				console.info( `[img-pop] no: ${btn}` )
			}
		}
	}
} );
