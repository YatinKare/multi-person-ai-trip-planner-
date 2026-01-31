set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.generate_invite_code()
 RETURNS text
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$                                                                                                    
  DECLARE                                                                                                               
      chars TEXT := 'abcdefghijklmnopqrstuvwxyz0123456789';                                                             
      result TEXT := '';                                                                                                
      i INTEGER;                                                                                                        
      code_exists BOOLEAN := TRUE;                                                                                      
  BEGIN                                                                                                                 
      WHILE code_exists LOOP                                                                                            
          result := '';                                                                                                 
          FOR i IN 1..8 LOOP                                                                                            
              result := result || substr(chars, floor(random() * length(chars) + 1)::int, 1);                           
          END LOOP;                                                                                                     
          SELECT EXISTS(SELECT 1 FROM trips WHERE invite_code = result) INTO code_exists;                               
      END LOOP;                                                                                                         
      RETURN result;                                                                                                    
  END;                                                                                                                  
  $function$
;

CREATE OR REPLACE FUNCTION public.is_trip_creator(trip_uuid uuid, user_uuid uuid)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$                                                                                                 
  BEGIN                                                                                                                 
      RETURN EXISTS (                                                                                                   
          SELECT 1 FROM trips                                                                                           
          WHERE id = trip_uuid                                                                                          
          AND created_by = user_uuid                                                                                    
      );                                                                                                                
  END;                                                                                                                  
  $function$
;

CREATE OR REPLACE FUNCTION public.is_trip_member(trip_uuid uuid, user_uuid uuid)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$                                                                                                 
  BEGIN                                                                                                                 
      RETURN EXISTS (                                                                                                   
          SELECT 1 FROM trip_members                                                                                    
          WHERE trip_id = trip_uuid                                                                                     
          AND user_id = user_uuid                                                                                       
      );                                                                                                                
  END;                                                                                                                  
  $function$
;


