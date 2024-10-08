(define (convert-to-bmp filename heightmapfile outputname)
	(let* (
			(image (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
			(drawable (car (gimp-image-get-active-layer image)))
		)
		
		(gimp-image-convert-grayscale image)
		
		(gimp-drawable-levels
			drawable
			0
			(/ 93 255)
			1
			TRUE
			1
			(/ 93 255)
			1
			TRUE
		)
		
		(gimp-file-save RUN-NONINTERACTIVE image drawable heightmapfile heightmapfile)
		
		(if (not (= (car (gimp-image-base-type image)) RGB))
			(gimp-image-convert-rgb image))
		
		(gimp-image-scale image 2048 1408)
		
		(plug-in-normalmap
			RUN-NONINTERACTIVE
			image				
			drawable			
			0					
			0					
			50					
			1					
			0					
			0					
			0					
			0					
			0					
			1					
			0					
			0					
			drawable			
		)
		
		(gimp-file-save RUN-NONINTERACTIVE image drawable outputname outputname)
		(gimp-image-delete image)
	)
)

(convert-to-bmp "heightmap.png" "heightmap.bmp" "world_normal.bmp")
(gimp-quit 0)