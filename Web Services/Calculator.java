package com.unique;

import javax.jws.WebService;
import javax.jws.WebMethod;
import javax.jws.WebParam;

/**
 *
 * @author DELL
 */
@WebService(serviceName = "Calculator")
public class Calculator {

    /**
     * This is a sample web service operation
     */
    @WebMethod(operationName = "getmethod")
    public int getmethod(
        @WebParam(name = "parameter1") int parameter1, 
        @WebParam(name = "parameter2") int parameter2
    ) {
        int sum = parameter1 + parameter2;
        return sum;
    }
}