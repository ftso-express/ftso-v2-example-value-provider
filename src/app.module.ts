import { Module } from "@nestjs/common";
import { ExampleProviderService } from "./app.service";
import { ExampleProviderController } from "./app.controller";
import { CcxtFeed } from "./data-feeds/ccxt-provider-service";
import { RandomFeed } from "./data-feeds/random-feed";
import { BaseDataFeed } from "./data-feeds/base-feed";
import { FixedFeed } from "./data-feeds/fixed-feed";

@Module({
  imports: [],
  controllers: [ExampleProviderController],
  providers: [
    {
      provide: "EXAMPLE_PROVIDER_SERVICE",
      // The useFactory provider dynamically selects the data feed implementation
      // based on the `VALUE_PROVIDER_IMPL` environment variable.
      useFactory: async () => {
        let dataFeed: BaseDataFeed;

        // If VALUE_PROVIDER_IMPL is set to "fixed", use the FixedFeed provider.
        if (process.env.VALUE_PROVIDER_IMPL == "fixed") {
          dataFeed = new FixedFeed();
          // If VALUE_PROVIDER_IMPL is set to "random", use the RandomFeed provider.
        } else if (process.env.VALUE_PROVIDER_IMPL == "random") {
          dataFeed = new RandomFeed();
          // Otherwise, default to the CcxtFeed provider.
        } else {
          const ccxtFeed = new CcxtFeed();
          await ccxtFeed.start();
          dataFeed = ccxtFeed;
        }

        // Instantiate the ExampleProviderService with the selected data feed.
        const service = new ExampleProviderService(dataFeed);
        return service;
      },
    },
  ],
})
export class AppModule {}
