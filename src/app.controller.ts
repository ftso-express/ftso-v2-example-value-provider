import { Body, Controller, Param, DefaultValuePipe, ParseIntPipe, Post, Inject, Logger, Query } from "@nestjs/common";
import { ApiTags } from "@nestjs/swagger";
import { ExampleProviderService } from "./app.service";
import {
  FeedValuesRequest,
  FeedValuesResponse,
  FeedVolumesResponse,
  RoundFeedValuesResponse,
} from "./dto/provider-requests.dto";

@ApiTags("Feed Value Provider API")
@Controller()
export class ExampleProviderController {
  private logger = new Logger(ExampleProviderController.name);

  constructor(@Inject("EXAMPLE_PROVIDER_SERVICE") private readonly providerService: ExampleProviderService) {}

  /**
   * Retrieves feed values for a specific voting round.
   * Used by FTSOv2 Scaling clients.
   * @param votingRoundId - The ID of the voting round.
   * @param body - The request body containing the feed IDs.
   * @returns The feed values for the specified voting round.
   */
  @Post("feed-values/:votingRoundId")
  async getFeedValues(
    @Param("votingRoundId", ParseIntPipe) votingRoundId: number,
    @Body() body: FeedValuesRequest
  ): Promise<RoundFeedValuesResponse> {
    const values = await this.providerService.getValues(body.feeds);
    this.logger.log(`Feed values for voting round ${votingRoundId}: ${JSON.stringify(values)}`);
    return {
      votingRoundId,
      data: values,
    };
  }

  /**
   * Retrieves the latest feed values without a specific voting round ID.
   * Used by FTSOv2 Fast Updates clients.
   * @param body - The request body containing the feed IDs.
   * @returns The latest feed values.
   */
  @Post("feed-values/")
  async getCurrentFeedValues(@Body() body: FeedValuesRequest): Promise<FeedValuesResponse> {
    const values = await this.providerService.getValues(body.feeds);
    this.logger.log(`Current feed values: ${JSON.stringify(values)}`);
    return {
      data: values,
    };
  }

  /**
   * Retrieves the trading volumes for the requested feeds over a specified time window.
   * @param body - The request body containing the feed IDs.
   * @param windowSec - The time window in seconds for which to retrieve the volume. Defaults to 60.
   * @returns The trading volumes for the requested feeds.
   */
  @Post("volumes/")
  async getFeedVolumes(
    @Body() body: FeedValuesRequest,
    @Query("window", new DefaultValuePipe("60"), ParseIntPipe) windowSec: number
  ): Promise<FeedVolumesResponse> {
    const values = await this.providerService.getVolumes(body.feeds, windowSec);
    this.logger.log(`Feed volumes for last ${windowSec} seconds: ${JSON.stringify(values)}`);
    return {
      data: values,
    };
  }
}
