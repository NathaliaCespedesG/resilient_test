import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Users } from '../shared/models/database-types';

@Injectable({
  providedIn: 'root'
})
export class RequestsService {

  private baseUrl = 'http://localhost:8000/api/';

  constructor(private http: HttpClient) { }

  addParticipant(participantData: any): Observable<any> {
    const reqUrl = this.baseUrl + 'users/';

    return this.http.post<any>(reqUrl, participantData);
  }

  editParticipant(participantData: any): Observable<any> {
    const reqUrl = this.baseUrl + 'user/' + participantData.userId + '/';

    // if (Object.keys(participantData).length  2) {
    //   return this.http.put<any>(reqUrl, participantData);
    // }

    return this.http.patch<any>(reqUrl, participantData);
  }

  getUsers(): Observable<Users> {
    const usersUrl = this.baseUrl + 'users/';

    return this.http.get<Users>(usersUrl);
  }

  getDevicesByUsername(username: string): Observable<any>{
    const devicesUrl = this.baseUrl + 'devices/?username=' + username;

    return this.http.get<any>(devicesUrl);
  }

  getDeviceSummaryByUsername(username: string, device_type: string): Observable<any>{
    const devicesUrl = this.baseUrl + device_type + '/summary/?username=' + username;

    return this.http.get<any>(devicesUrl);

  }

}
